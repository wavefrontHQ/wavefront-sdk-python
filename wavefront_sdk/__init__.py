"""Wavefront Python SDK.

This library provides support for sending metrics, histograms and opentracing
spans to Wavefront via proxy or direct ingestion.

@author Hao Song (songhao@vmware.com)
"""

import pkg_resources

from .client_factory import WavefrontClientFactory


__all__ = ['WavefrontClientFactory']

__version__ = None

try:
    __version__ = pkg_resources.get_distribution(
            'wavefront-sdk-python').version
except pkg_resources.DistributionNotFound:
    # __version__ is only available when distribution is installed.
    pass
