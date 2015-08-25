'''
For wrapper
'''

import datetime
import os
from setuptools import setup, find_packages


NAME = 'Chris Lane'
AUTHOR = 'Chris Lane'
AUTHOR_EMAIL = 'chris@lane-jayasinha.com'
URL = 'https://github.com/lanstin/wrapper'

if __name__ == '__main__':
    VERSION = "0.0.1"
    setup(name=NAME,
          version=VERSION,
          author=AUTHOR,
          author_email=AUTHOR_EMAIL,
          url=URL,
          packages=find_packages(exclude=('test', 'test.*')),
          include_package_data=True)
