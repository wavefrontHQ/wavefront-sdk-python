# -*- coding: utf-8 -*-
"""Wavefront Python SDK.

This library provides support for sending metrics, histograms and opentracing
spans to Wavefront via proxy or direct ingestion.

@author Hao Song (songhao@vmware.com)
"""
import pkg_resources

from wavefront_sdk.direct import WavefrontDirectClient
from wavefront_sdk.proxy import WavefrontProxyClient

__all__ = ['WavefrontDirectClient', 'WavefrontProxyClient']
__version__ = pkg_resources.get_distribution('wavefront-sdk-python').version
