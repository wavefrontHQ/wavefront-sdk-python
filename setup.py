#!/usr/bin/env python3
"""VMware Aria Operations for Applications Python SDK."""

import os

import setuptools

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                       'README.md')) as fd:
    LONG_DESCRIPTION = fd.read()

setuptools.setup(
    name='wavefront-sdk-python',
    version='2.0.0',  # Please update with each pull request.
    author='VMware Aria Operations for Applications Team',
    url='https://github.com/wavefrontHQ/wavefront-sdk-python',
    license='Apache-2.0',
    description='VMware Aria Operations for Applications Python SDK',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    keywords=[
        'Aria',
        'Aria Operations',
        'Aria Operations for Applications',
        '3D Observability',
        'Distributed Tracing',
        'Histograms',
        'Logging',
        'Metrics',
        'Monitoring',
        'Observability',
        'Tracing',
        'VMware Aria',
        'VMware Aria Operations',
        'VMware Aria Operations for Applications',
        'Wavefront',
        'Wavefront SDK'
        ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Networking :: Monitoring'
        ],
    include_package_data=True,
    packages=setuptools.find_packages(exclude=('*.tests', '*.tests.*',
                                               'tests.*', 'tests')),
    install_requires=(
        'requests>=2.27',
        'tdigest>=0.5.2',
        'Deprecated>=1.2.10'
        )
)
