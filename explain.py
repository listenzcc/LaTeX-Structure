# File: explain.py
# Aim: Parse a LaTeX file

import sys
import webbrowser
from Package.LaTeX_tools import LaTeX_Parser

# Get path using the 2nd element from input,
# or use the file of './main.tex' as the path
if len(sys.argv) > 1:
    path = sys.argv[1]
else:
    path = './main.tex'


def main(path=path):
    # Main function,
    # call LaTeX Parser and use it
    ltxp = LaTeX_Parser(path)
    ltxp.read_file()
    features = ltxp.parse_features()
    features.to_html('a.html')
    webbrowser.open('a.html')


if __name__ == '__main__':
    # Main function caller
    main()
