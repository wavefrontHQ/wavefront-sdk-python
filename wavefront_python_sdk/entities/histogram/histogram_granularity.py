from __future__ import absolute_import, division, print_function

from enum import Enum


class HistogramGranularity(Enum):
    MINUTE = "!M"
    HOUR = "!H"
    DAY = "!D"

    def __init__(self, identifier):
        self.identifier = identifier
