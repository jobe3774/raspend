#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  
#  License: MIT
#  
#  Copyright (c) 2019 Joerg Beckers

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="raspend",
    version="1.2.0",
    author="Joerg Beckers",
    author_email="pypi@jobe-software.de",
    description="A small and easy to use HTTP backend framework for the Raspberry Pi which is ideal for small to medium-sized home automation projects.",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jobe3774/raspend.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Home Automation",
    ],
    python_requires='>=3.5',
)