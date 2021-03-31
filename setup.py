#!/usr/bin/env python3
"""Wavefront Python SDK.

<p>This is a Wavefront Python SDK</p>
"""

import os

import setuptools

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                       'README.md')) as fd:
    LONG_DESCRIPTION = fd.read()

setuptools.setup(
    name='wavefront-sdk-python',
    version='1.8.0',
    author='Wavefront by VMware',
    author_email='chitimba@wavefront.com',
    url='https://github.com/wavefrontHQ/wavefront-sdk-python',
    license='Apache-2.0',
    description='Wavefront Python SDK',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    keywords=[
        'Wavefront',
        'Wavefront SDK'
        ],
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
        ],
    include_package_data=True,
    packages=setuptools.find_packages(exclude=('*.tests', '*.tests.*',
                                               'tests.*', 'tests')),
    install_requires=(
        'requests>=2.18.4',
        'tdigest>=0.5.2',
        'Deprecated>=1.2.10'
        )
)
