# File: __init__.py
# Package: LaTeX-Structure
# Usage: Parse the structure of a LaTeX file,
#        and provide useful web application,
#        to generate useful appendix context

import configparser
import logging
import logging.config
import os

PACKAGE_FOLDER = os.path.dirname(__file__)


def _get(name, folder=PACKAGE_FOLDER):
    return os.path.join(folder, '..', name)


CONFIG = configparser.ConfigParser()
CONFIG.read(_get('setting.ini'))

logging.config.fileConfig(_get('logging.conf'))

# create logger
LOGGER = logging.getLogger('debugLogger')

# 'application' code
LOGGER.info('LaTeX Structure Parsing Package is initialized.')
# LOGGER.debug('Debug message')
# LOGGER.info('Info message')
# LOGGER.warning('Warn message')
# LOGGER.error('Error message')
# LOGGER.critical('Critical message')
