# -*- coding: utf-8 -*-
"""Span Log.

@author Hao Song (songhao@vmware.com)`
"""


class SpanLog(object):

    def __init__(self, timestamp, fields):
        self.timestamp = timestamp
        self.fields = fields
