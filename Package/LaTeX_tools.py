# File: LaTeX_tools.py
# Aim: Get content of LaTeX file

import pandas as pd
from tqdm.auto import tqdm
from . import LOGGER, CONFIG

feature_levels = CONFIG['FeatureLevels']
feature_keys = CONFIG['FeatureKeys']
feature_others = CONFIG['FeatureOthers']


def startswith_feature(line,
                       features=[feature_levels,
                                 feature_keys,
                                 feature_others]):
    # Check if the [line] startswith keys in features
    # Regularize the [line]
    line = line.strip()

    for feats in features:
        if any([line.startswith(f'\\{e}') for e in feats]):
            return True

    return False


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
        columns = ['Key', 'Name', 'Label',
                   'Tracking', 'ExpandTo',
                   'Level', 'Seek', 'LineCount']
        features = pd.DataFrame(columns=columns)

        # Init values
        level = 0
        tracking = []
        inner_count = 0
        begin_iloc = 0

        for line in tqdm(self.feature_lines):
            # Parse the line
            content, seek, line_count = line
            key = content.split('{')[0][1:]
            name = content.split('{', 1)[1][:-1]

            dct = dict(
                Name=name,
                Key=key,
                Seek=seek,
                LineCount=line_count,
            )

            if '\\label' in name:
                LOGGER.warning(', '.join([
                    f'Detecting misplaced "\\label" define in line {line_count}',
                    'it means you put "\\label" define block in the same line of something like "\\begin"',
                    'it can be fixed',
                    'however it is not recommended', ]))

            if any([key == 'begin' and name == 'document',
                    key == 'end' and name == 'document']):
                features = features.append(pd.Series(dct),
                                           ignore_index=True)
                continue

            # New record will be append to the existing [features] DataFrame,
            # so, the current iloc equals to the length of [features]
            current_iloc = len(features)

            # Operation on conditions
            if key in feature_levels:
                level = int(feature_levels[key])
                # Modify the [tracking] based on [_level] and [level]
                while len(tracking):
                    if level > features.iloc[tracking[-1]]['Level']:
                        break
                    tracking.pop()
                tracking.append(current_iloc)
                dct = dict(dct,
                           Tracking=tracking.copy(),
                           Level=level,)

            # Inner count
            # Match begin
            if key == 'begin':
                if inner_count == 0:
                    begin_iloc = current_iloc
                inner_count += 1

                # ! Try to handle the issue of same-line-label
                if '\\label{' in name:
                    _name, _label = name.split('\\label{', 1)

                    _name = _name.strip()
                    if _name.endswith('}'):
                        _name = _name[:-1]

                    _label = _label.strip()

                    dct = dict(dct,
                               Name=_name,
                               Label=_label)
            # Match end
            if key == 'end':
                # ! \\end can not overcount \\begin
                try:
                    assert(inner_count > 0)
                except AssertionError as err:
                    LOGGER.error(', '.join([f'Found "end" without "begin" in line "{line_count}"',
                                            'this always means an incorrect .tex file is being processed',
                                            'please check it.']))
                    raise AssertionError(err)

                inner_count -= 1

                # When [inner_count] equals to zero,
                # it means the begin ends here
                if inner_count == 0:
                    # ! The name of the end has to equal with its begin
                    try:
                        assert(features['Name'].iloc[begin_iloc] == name)
                    except AssertionError as err:
                        _line_count = features['LineCount'].iloc[begin_iloc]
                        LOGGER.error(', '.join([f'Found "end" mismatch with "begin" in line "{line_count}"',
                                                f'the detected "begin" line is "{_line_count}"',
                                                'this always means something wrong within the block between begin and end']))
                        raise AssertionError(err)
                    features['ExpandTo'].iloc[begin_iloc] = current_iloc
            # Match label
            if key == 'label':
                features['Label'].iloc[begin_iloc] = name

            # Record the [line]
            features = features.append(pd.Series(
                dct),
                #     dict(
                #     Name=name,
                #     Key=key,
                #     Tracking=tracking.copy(),
                #     Level=level,
                #     Seek=seek,
                #     LineCount=line_count,
                # )),
                ignore_index=True)

        # Select and re-order the columns
        features = features[columns]
        features[features.isna()] = '-'
        print(features)
        self.features = features
        return features
