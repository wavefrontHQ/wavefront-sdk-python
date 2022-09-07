"""Wavefront implementation of a histogram.

@author: Hao Song (songhao@vmware.com)
"""
from __future__ import division
# pylint: disable=E0012,R0205

import math
import threading
import time

import tdigest


class Snapshot(object):
    """Wrapper for TDigest distribution."""

    def __init__(self, dist):
        """Construct TDigest Wrapper.

        @param dist: tdigest.TDigest
        @type dist: tdigest.TDigest
        """
        self.distribution = dist

    def get_max(self):
        """Get the maximum value in the distribution.

        @return: Maximum value
        """
        try:
            max_val = self.distribution.percentile(100)
        except ValueError:
            max_val = None
        return max_val

    def get_min(self):
        """Get the minimum value in the distribution.

        @return: minimum value
        """
        try:
            min_val = self.distribution.percentile(0)
        except ValueError:
            min_val = None
        return min_val

    def get_mean(self):
        """Get the mean of the values in the distribution.

        @return: mean value
        """
        try:
            return self.distribution.trimmed_mean(0, 100)
        except ZeroDivisionError:
            return None
        # Equivalent approach:
        # centroids = self.distribution.centroids_to_list()
        # if not centroids:
        #     return None
        # return sum(c['c'] * c['m'] for c in centroids) / sum(c['c'] for c in
        #                                                      centroids)

    def get_sum(self):
        """Get the sum of the values in the distribution.

        @return: sum of value
        """
        centroids = self.distribution.centroids_to_list()
        return sum(c['c'] * c['m'] for c in centroids)

    def get_value(self, quantile):
        """Get the value of given quantile.

        @param quantile: Quantile, range from 0 to 1
        @type quantile: float
        @return: the value in the distribution at the given quantile.
        Return None if distribution is empty.
        """
        percentile = quantile * 100
        try:
            return self.distribution.percentile(percentile)
        except ValueError:
            # ValueError("Tree is empty") from TDigest
            return None

    def get_size(self):
        """Get the size of snapshot.

        @return: Size of snapshot.
        """
        return self.distribution.n

    def get_count(self):
        """Get the number of values in the distribution.

        @return: Number of values
        """
        return self.get_size()


class Distribution(object):
    """Representation of a histogram distribution.

    Containing a timestamp and a list of centroids.
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, timestamp, centroids):
        """Construct a distribution.

        @param timestamp: Timestamp in milliseconds since the epoch.
        @type timestamp: long
        @param centroids: Centroids
        @type centroids: list of tuple
        """
        self.timestamp = timestamp
        self.centroids = centroids


class ThreadMinuteBin(object):
    """Representation of a bin holds all threads histogram data in a min."""

    # pylint: disable=too-few-public-methods
    def __init__(self, accuracy=100, minute_millis=None):
        """Construct the Minute Bin.

        @param accuracy: Accuracy range from [0, 100]
        @type accuracy: int
        @param minute_millis: The timestamp at the start of the minute.
        @type minute_millis: long
        """
        self.accuracy = accuracy
        self.minute_millis = minute_millis
        self.per_thread_dist = {}

    def get_dist_by_thread_id(self, thread_id):
        """Retrieve the thread-local dist in one given minute."""
        if thread_id not in self.per_thread_dist:
            self.per_thread_dist[thread_id] = tdigest.TDigest(delta=1 /
                                                              self.accuracy)
        return self.per_thread_dist[thread_id]

    def update_dist_by_thread_id(self, thread_id, value):
        """Update the value in the distribution of given thread id."""
        self.get_dist_by_thread_id(thread_id).update(value)

    def bulk_update_dist_by_thread_id(self, thread_id, means, counts):
        """Bulk update values in the distribution of given thread id."""
        if means and counts:
            current_bin = self.get_dist_by_thread_id(thread_id)
            for i in range(min(len(means), len(counts))):
                current_bin.update(means[i], counts[i])

    def get_centroids(self):
        """Get list of centroids for dists of all threads in this minute."""
        centroids = []
        for _, digest in self.per_thread_dist.items():
            centroids.extend(digest.centroids_to_list())
        return centroids

    def to_distribution(self):
        """Convert to Distribution."""
        distributions = []
        for _, digest in self.per_thread_dist.items():
            centroids = [(centroid['m'], int(centroid['c'])) for centroid in
                         digest.centroids_to_list()]
            distributions.append(
                Distribution(self.minute_millis, centroids))
        return distributions


class WavefrontHistogramImpl(object):
    """Wavefront implementation of a histogram."""

    # Accuracy = Compression = 1 / Delta.
    _ACCURACY = 100

    # If a thread's bin queue has exceeded MAX_BINS number of bins (e.g.,
    # the thread has data that has yet to be reported for more than MAX_BINS
    # number of minutes), delete the oldest bin. Defaulted to 10 because we
    # can expect the histogram to be reported at least once every 10 minutes.
    _MAX_BINS = 10

    def __init__(self, clock_millis=None):
        """Construct Wavefront Histogram.

        @param clock_millis: A function which returns timestamp.
        @type clock_millis: function
        """
        self._clock_millis = clock_millis or self.current_clock_millis
        self._prior_minute_bins_list = []
        self._lock = threading.RLock()
        self._current_minute_bin = ThreadMinuteBin(
            self._ACCURACY, self.current_minute_millis())

    @staticmethod
    def current_clock_millis():
        """Get current time in millisecond."""
        return time.time() * 1000

    def current_minute_millis(self):
        """Get the timestamp of start of certain minute."""
        return int(self._clock_millis() / 60000) * 60000

    def update(self, value):
        """Add one value to the distribution.

        @param value: value to add.
        @type value: float
        """
        self.get_current_bin().update_dist_by_thread_id(
            threading.current_thread().ident, value)

    def bulk_update(self, means, counts):
        """Bulk-update this histogram with a set of centroids.

        @param means: the centroid values
        @type means: list of float
        @param counts: the centroid weights/sample counts
        @type counts: list of int
        """
        self.get_current_bin().bulk_update_dist_by_thread_id(
            threading.current_thread().ident, means, counts)

    def get_current_bin(self):
        """Retrieve the current bin.

        Will be invoked on the thread local histogram_bins_list.
        @return: Current minute bin
        @rtype: ThreadMinuteBin
        """
        return self.get_or_update_current_bin(self.current_minute_millis())

    def get_or_update_current_bin(self, curr_minute_millis):
        """Get current minute bin.

        Will update _prior_minute_bins_list if the minute has passed.
        @param curr_minute_millis: Current minute in millis
        @return: ThreadMinuteBin of current minute.
        @rtype: ThreadMinuteBin
        """
        if self._current_minute_bin.minute_millis == curr_minute_millis:
            return self._current_minute_bin
        # only one update thread can flush the current bin to
        # _prior_minute_bins_list and update the current bin.
        with self._lock:
            # Double check the minute millis of current bin to avoid if there
            # are multiple threads entering this block and the first thread
            # already did the flushing.
            if self._current_minute_bin.minute_millis != curr_minute_millis:
                if len(self._prior_minute_bins_list) > self._MAX_BINS:
                    del self._prior_minute_bins_list[0]
                self._prior_minute_bins_list.append(self._current_minute_bin)
                self._current_minute_bin = ThreadMinuteBin(self._ACCURACY,
                                                           curr_minute_millis)
            return self._current_minute_bin

    def get_prior_minute_bins_list(self):
        """Return newly-updated _prior_minute_bins_list."""
        self.get_or_update_current_bin(self.current_minute_millis())
        return self._prior_minute_bins_list

    def std_dev(self):
        """Return the stdDev of the values in the distribution."""
        mean = self.get_mean()
        variance_sum = 0
        count = 0
        for minute_bin in self.get_prior_minute_bins_list():
            centroids = minute_bin.get_centroids()
            count += sum(c['c'] for c in centroids)
            variance_sum += sum(c['c'] * ((c['m'] - mean) ** 2) for c in
                                centroids)
        variance = 0 if count == 0 else variance_sum / count
        return math.sqrt(variance)

    def flush_distributions(self):
        """Aggregate all the minute bins prior to the current minute.

        Only aggregating before current minute is because threads might be
        updating the current minute bin while the method is invoked.

        Returns a list of the distributions held within each bin.

        Note that invoking this method will also clear all data from the
        aggregated bins, thereby changing the state of the system and
        preventing data from being flushed more than once.

        @return: list of the distributions held within each bin
        @rtype: list of Distribution
        """
        distributions = []
        self.get_or_update_current_bin(self.current_minute_millis())
        with self._lock:
            for minute_bin in self._prior_minute_bins_list[:]:
                distributions.extend(minute_bin.to_distribution())
                self._prior_minute_bins_list.remove(minute_bin)
        return distributions

    def get_count(self):
        """Get the number of values in the distribution."""
        count = 0
        for minute_bin in self.get_prior_minute_bins_list():
            if minute_bin.per_thread_dist:
                count += sum(dist.n for dist
                             in minute_bin.per_thread_dist.values())
        return count

    def get_sum(self):
        """Get the sum of the values in the distribution."""
        res = 0
        for minute_bin in self.get_prior_minute_bins_list():
            res += sum(c['c'] * c['m'] for c in minute_bin.get_centroids())
        return res

    def get_snapshot(self):
        """Return a statistical of the histogram distribution.

        @return: Snapshot of Histogram
        @rtype: Snapshot
        """
        snapshot = tdigest.TDigest(1 / self._ACCURACY)
        for minute_bin in self.get_prior_minute_bins_list():
            for thread_id in minute_bin.per_thread_dist:
                snapshot = snapshot + minute_bin.per_thread_dist[thread_id]
        return Snapshot(snapshot)

    def get_max(self):
        """Get the maximum value in the distribution.

        Return None if the distribution is empty.
        """
        max_val = float('-inf')
        for minute_bin in self.get_prior_minute_bins_list():
            if minute_bin.per_thread_dist:
                max_val = max(max(dist.percentile(100) for dist
                                  in minute_bin.per_thread_dist.values()),
                              max_val)
        return None if float('-inf') == max_val else max_val

    def get_min(self):
        """Get the minimum value in the distribution.

        Return None if the distribution is empty.
        """
        min_val = float('inf')
        for minute_bin in self.get_prior_minute_bins_list():
            if minute_bin.per_thread_dist:
                min_val = min(min(dist.percentile(0) for dist
                                  in minute_bin.per_thread_dist.values()),
                              min_val)
        return None if float('inf') == min_val else min_val

    def get_mean(self):
        """Get the mean of the values in the distribution.

        Return None if the distribution is empty.
        """
        count = total = 0
        for minute_bin in self.get_prior_minute_bins_list():
            centroids = minute_bin.get_centroids()
            count += sum(c['c'] for c in centroids)
            total += sum(c['c'] * c['m'] for c in centroids)
        if count == 0:
            return None
        return total / count
