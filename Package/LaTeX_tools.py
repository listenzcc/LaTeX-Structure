# File: LaTeX_tools.py
# Aim: Get content of LaTeX file

from . import LOGGER, CONFIG

feature_levels = CONFIG['FeatureLevels']
feature_keys = CONFIG['FeatureKeys']


def startswith_feature(line, levels=feature_levels, keys=feature_keys):
    if any([line.startswith(f'\\{e}') for e in levels]):
        return True

    if any([line.startswith(f'\\{e}') for e in keys]):
        return True

    return False


class LaTeX_Parser(object):
    def __init__(self, path):
        self.path = path

    def read_file(self):
        with open(self.path, 'r') as f:
            lines = f.readlines()
        LOGGER.info(f'Read "{len(lines)}" lines from "{self.path}"')

    def parse_file(self):
        feature_lines = []
        with open(self.path, 'r') as f:
            while True:
                line = f.readline()
                if not line:
                    break
                line = line.strip()
                if startswith_feature(line):
                    feature_lines.append(line)
        LOGGER.info(
            f'Parsed "{len(feature_lines)}" feature lines from "{self.path}"')
        for j, feat in enumerate(feature_lines):
            print(j, feat)
        self.feature_lines = feature_lines
        return feature_lines
