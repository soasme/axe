#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='Axe',
    version='0.0.1',
    url='https://www.github.com/soasme/axe/',
    author='Ju Lin',
    author_email='soasme@gmail.com',
    description='An eXtremely Extendable Python Web Framework',
    packages=find_packages(exclude=['tests']),
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    test_suite = 'py.test',
    install_requires=[
        'Werkzeug',
    ],
    tests_require=['pytest', 'mock>=0.8'],
)