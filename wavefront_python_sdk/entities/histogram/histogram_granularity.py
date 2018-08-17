from __future__ import absolute_import, division, print_function


class HistogramGranularity(object):
    """
    Granularity (minute /hour / day)
    by which histograms distributions are aggregated.
    """
    MINUTE = "!M"
    HOUR = "!H"
    DAY = "!D"
