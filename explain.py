# File: explain.py
# Aim: Parse a LaTeX file

import sys
from Package.LaTeX_tools import LaTeX_Parser

if len(sys.argv) > 1:
    path = sys.argv[1]
else:
    path = './main.tex'

if __name__ == '__main__':
    ltxp = LaTeX_Parser(path)
    ltxp.read_file()
    ltxp.parse_file()
