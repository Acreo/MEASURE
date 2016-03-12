__author__ = 'eponsko'
from setuptools import setup, find_packages
setup(name='measureparser',
      version='0.1',
      description='Parser for the MEASURE languange',
      url='http://acreo.github.io/MEASURE/',
      author='ponsko',
      author_email='ponsko@acreo.se',
      license='LGPLv2.1',
      packages = find_packages(),
      requires=['pyparsing', 'json', 'yaml'])
