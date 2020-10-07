# -*- coding: utf-8 -*-
"""Wavefront SDK Delta Counter.

@author Joanna Ko (joannak@vmware.com)
"""
from wavefront_sdk.common.metrics.counter import WavefrontSdkCounter


class WavefrontSdkDeltaCounter(WavefrontSdkCounter):
    """Wavefront SDK Delta Counter. Delta Counters measures change since metric
    was last recorded, and is prefixed with \u2206 (∆ - INCREMENT) or
    \u0394 (Δ - GREEK CAPITAL LETTER DELTA)."""
    pass
