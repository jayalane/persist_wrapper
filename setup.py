'''
For wrapper
'''

import datetime
import os
from setuptools import setup, find_packages


NAME = 'persist-wrapper'
AUTHOR = 'Chris Lane'
AUTHOR_EMAIL = 'chris@lane-jayasinha.com'
URL = 'https://github.com/jayalane/persist_wrapper'

if __name__ == '__main__':
    VERSION = "0.0.43"
    setup(name=NAME,
          version=VERSION,
          description="Utility to cache date-based data",
          author=AUTHOR,
          author_email=AUTHOR_EMAIL,
          url=URL,
          license = "BSD",
          classifiers = [
              'Development Status :: 3 - Alpha',
              'License :: OSI Approved :: BSD License',
          ],
          packages=['date_data_cache'])
