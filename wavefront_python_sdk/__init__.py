"""
Wavefront Python SDK.

This library provides support for sending metrics, histograms and opentracing
spans to Wavefront via proxy or direct ingestion.

@author Hao Song (songhao@vmware.com)
"""
__version__ = '0.1.0'

from wavefront_python_sdk.direct import WavefrontDirectClient
from wavefront_python_sdk.proxy import WavefrontProxyClient

__all__ = ['WavefrontDirectClient', 'WavefrontProxyClient', 'common']
