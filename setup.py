# -*- coding: utf-8 -*-
"""
# Axe

Axe is a Python Generative AI toolkit.
It offers a set of tools for building AI framework easier.


## Where can I get help?

Please report issues on [Github Issue](https://github.com/soasme/axe/issues).
Read documentation here: http://axe.rtfd.org
"""

from setuptools import setup

setup(
    name="Axe",
    version='0.0.5',
    author="Ju Lin",
    author_email="soasme@gmail.com",
    description="Axe is a Python Generative AI toolkit",
    long_description=__doc__,
    license="MIT License",
    keywords="AI,GPT,GenerativeAI,Transformer",
    url="https://github.com/soasme/axe",
    packages=['axe'],
    classifiers=[
        "Development Status :: 4 - Beta",
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        "License :: OSI Approved :: MIT License",
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
