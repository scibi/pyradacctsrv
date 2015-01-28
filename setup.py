#!/usr/bin/env python
# coding: utf-8

import setuptools

try:
    from pypandoc import convert
    read_md = lambda f: convert(f, 'rst')
except ImportError:
    print("warning: pypandoc module not found, could not convert Markdown to RST")
    read_md = lambda f: open(f, 'r').read()

setuptools.setup(
    name="pyradacctsrv",
    version="0.1.0",
    url="https://github.com/scibi/pyradacctsrv",

    author="Patryk Ściborek",
    author_email="patryk@sciborek.com",

    description="RADIUS Accounting server implemented in Python",
    long_description=read_md('README.md'),

    packages=setuptools.find_packages(),

    install_requires=[],

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ],
)
