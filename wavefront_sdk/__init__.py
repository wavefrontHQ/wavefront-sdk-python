"""Wavefront Python SDK.

This library provides support for sending metrics, histograms and opentracing
spans to Wavefront via proxy or direct ingestion.

@author Hao Song (songhao@vmware.com)
"""


from .client_factory import WavefrontClientFactory


__all__ = ['WavefrontClientFactory']

__version__ = None

try:
    import importlib.metadata
    try:
        __version__ = importlib.metadata.version('wavefront-sdk-python')
    except importlib.metadata.PackageNotFoundError:
        # __version__ is only available when distribution is installed.
        pass
except ImportError:
    pass
