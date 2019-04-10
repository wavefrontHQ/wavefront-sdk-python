# -*- coding: utf-8 -*-

"""Wavefront Python SDK.

This library provides support for sending metrics, histograms and opentracing
spans to Wavefront via proxy or direct ingestion.

@author Hao Song (songhao@vmware.com)
"""
import pkgutil

from wavefront_sdk.direct import WavefrontDirectClient
from wavefront_sdk.proxy import WavefrontProxyClient

__version__ = pkgutil.get_distribution(
    'wavefront-sdk-python').metadata['version']

__all__ = ['WavefrontDirectClient',
           'WavefrontProxyClient']
