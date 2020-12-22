# File: LaTeX_tools.py
# Aim: Get content of LaTeX file

import pandas as pd
from tqdm.auto import tqdm
from . import LOGGER, CONFIG, TEMP_HTML_PATH

feature_levels = CONFIG['FeatureLevels']
feature_keys = CONFIG['FeatureKeys']
feature_others = CONFIG['FeatureOthers']
feature_controls = CONFIG['FeatureControls']
feature_labels = CONFIG['FeatureLabels']


def startswith_feature(line,
                       features=[
                           feature_levels, feature_keys, feature_others,
                           feature_controls, feature_labels
                       ]):
    # Check if the [line] startswith keys in features
    # Regularize the [line]
    line = line.strip()

    for feats in features:
        if any([line.startswith(f'\\{e}') for e in feats]):
            return True

    return False


def parse_row(row):
    # Parse single [row] of .text file,
    # ONLY parse control rows,
    # select key, params and value from the row.
    row = row.strip()
    if not row.startswith('\\'):
        return []

    split = [e.strip() for e in row.split('\\') if e]

    def _parse(s):
        key = '-'
        params = '-'
        value = '-'

        if '[' in s and '{' in s:
            # [s] has params, and has value
            key = s.split('[')[0]
            params = s.split('[')[1].split(']')[0]
            value = s.split('{')[1].split('}')[0]

        if '[' in s and '{' not in s:
            # [s] has params, and has no value
            key = s.split('[')[0]
            params = s.split('[')[1].split(']')[0]

        if '[' not in s and '{' in s:
            # [s] has no params, and has value
            key = s.split('{')[0]
            value = s.split('{')[1].split('}')[0]

        if '[' not in s and '{' not in s:
            # [s] has no params, and has no value
            key = s

        return dict(key=key, params=params, value=value)

    return [_parse(s) for s in split]


class LaTeX_Parser(object):
    # LaTeX Parser to find and parse all features
    def __init__(self, path, show_step=True):
        self.path = path
        self.show_step = show_step

    def read_file(self):
        # Read the file of [self.path]
        # ! Get and return the features as the order of written
        feature_lines = []
        count = 0
        with open(self.path, 'r') as f:
            while True:
                seek = f.tell()
                line = f.readline()
                count += 1
                if not line:
                    # Empty line means reaching the end of file
                    break

                if startswith_feature(line):
                    pair = [line.strip(), seek, count]
                    feature_lines.append(pair)
        LOGGER.info(
            f'Parsed "{len(feature_lines)}" feature lines from "{self.path}"')

        # Show steps
        if self.show_step:
            for feat in tqdm(feature_lines):
                print(feat)

        # A feature line is three elements array,
        # [content: raw content,
        #  seek: seek offset,
        #  count: line count]
        self.feature_lines = feature_lines
        return feature_lines

    def parse_features(self):
        # Parse the [self.feature_lines]
        columns = [
            'Key', 'Params', 'Value', 'Label', 'Tracking', 'ExpandTo', 'Level',
            'Seek', 'LineCount'
        ]
        features = pd.DataFrame(columns=columns)

        # Init values
        level = 0
        tracking = []
        inner_count = 0
        begin_iloc = 0

        for line in tqdm(self.feature_lines):
            # Parse the line
            content, seek, line_count = line
            for parsed in parse_row(content):
                key = parsed['key']
                params = parsed['params']
                value = parsed['value']

                # Init dct
                dct = dict(
                    Key=key,
                    Params=params,
                    Value=value,
                    Seek=seek,
                    LineCount=line_count,
                )

                if key in ['begin', 'end'] and value == 'document':
                    features = features.append(dct, ignore_index=True)
                    continue

                # New record will be append to the [features] DataFrame finally,
                # so, the "current_iloc" equals to the length of [features]
                current_iloc = len(features)

                # Operation on conditions
                # Get current [level] and pop tailing trackings until satisfying
                # the situation of [level] is LARGER than the latest tracking
                if key in feature_levels:
                    level = int(feature_levels[key])
                    while len(tracking):
                        if level > features.iloc[tracking[-1]]['Level']:
                            break
                        tracking.pop()
                    tracking.append(current_iloc)
                    dct = dict(dct, Tracking=tracking.copy(), Level=level)

                # Inner count
                # Match begin
                if key == 'begin':
                    if inner_count == 0:
                        begin_iloc = current_iloc
                    inner_count += 1

                # Match end
                if key == 'end':
                    # ! \\end can not overcount \\begin
                    try:
                        assert (inner_count > 0)
                    except AssertionError as err:
                        LOGGER.error(', '.join([
                            f'Found "end" without "begin" in line "{line_count}"',
                            'this always means an incorrect .tex file is being processed',
                            'please check it.'
                        ]))
                        raise err

                    inner_count -= 1

                    # When [inner_count] is less than or equals to zero,
                    # it means the begin ends here
                    if not inner_count > 0:
                        # ! The name of the end has to equal with its begin
                        try:
                            assert (
                                features['Value'].iloc[begin_iloc] == value)
                        except AssertionError as err:
                            _line_count = features['LineCount'].iloc[
                                begin_iloc]
                            LOGGER.error(', '.join([
                                f'Found "end" mismatch with "begin" in line "{line_count}"',
                                f'the detected "begin" line is "{_line_count}"',
                                'this always means something wrong within the block between begin and end'
                            ]))
                            raise err
                        features['ExpandTo'].iloc[begin_iloc] = current_iloc

                # Match label
                if key in feature_labels and inner_count == 1:
                    features['Label'].iloc[begin_iloc] = value

                # Record the [dct] finally
                features = features.append(pd.Series(dct), ignore_index=True)

                continue

        # Select and re-order the columns
        features = features[columns]
        features[features.isna()] = '-'
        print(features)
        self.features = features
        return features

    def generate_page(self):
        '''
        Generate interactive web page in HTML format,
        based on *features* generated by *self.parese_features*,
        contains three parts:
        - Features Area, print features as table
        - Outline Area, draw 1st-level features as tree-structure
        - Selected Area, print contents inside selected feature in Outline Area
        '''
        # Read html template
        html = open(TEMP_HTML_PATH).read()

        # ---------------------------------------------
        # Fill features
        features = self.features
        innerHTML_features = features.to_html(table_id='a')
        html = html.replace('<!-- Features Area -->', innerHTML_features)

        # ---------------------------------------------
        # Generate tree-structure,
        # fill outline
        innerHTML_tree = []
        state = dict(div_count=0, level=0)

        def _add(line, innerHTML_tree=innerHTML_tree):
            # Method of add [line] to innerHTML_tree
            innerHTML_tree.append(line)
            if line.startswith('<div'):
                state['div_count'] += 1
            if line.startswith('</div>'):
                state['div_count'] -= 1

        _add('<div class="branch">')

        def _wrap(key, value):
            # Method of generate wrapped html content of <[key]>value</key>
            return f'<{key}>{value}</{key}>'

        for i in range(len(features)):
            # Get the line of features
            se = features.iloc[i]

            # Tracking is not '-' means it is a title
            if not se['Tracking'] == '-':
                level = len(se['Tracking'])
                if level > state['level']:
                    for _ in range(level - state['level']):
                        _add('<div class="indent">')
                else:
                    for _ in range(state['level'] - level + 1):
                        _add('</div>')
                    _add('<div class="indent">')
                state['level'] = level
                h = f'h{level}'
                _add(_wrap(h, '{Key}: {Name}: {Label}'.format(**se)))
                continue

            # ExpandTo is not '-' means it is a beginner of a block
            if not se['ExpandTo'] == '-':
                _add(_wrap('p', '{Key}: {Name}: {Label}'.format(**se)))
                continue

            # Print subfile as plant-text
            if se['Key'] == 'subfile':
                _add(_wrap('p', '{Key}: {Name}: {Label}'.format(**se)))
                continue

        # Close the unclosed divs
        while state['div_count'] > 0:
            _add('</div>')

        innerHTML_tree = '\n'.join(innerHTML_tree)
        html = html.replace('<!-- Outline Area -->', innerHTML_tree)

        # ---------------------------------------------
        # Fill content
        content = open(self.path).read()
        # The code will be wrapped by <pre><code ...> as highlight.js requires
        content = '\n'.join(
            ['<pre><code class="tex">', content, '</code></pre>'])
        html = html.replace('<!-- Selected Area -->', content)

        return html
