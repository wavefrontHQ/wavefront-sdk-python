"""
Wavefront implementation of a histogram.

@author: Hao Song (songhao@vmware.com)
"""
from __future__ import division
import threading
import weakref
import time
from tdigest import TDigest


class Snapshot(object):
    """Wrapper for TDigest distribution."""

    def __init__(self, dist):
        """
        Construct TDigest Wrapper.

        @param dist: TDigest
        @type dist: TDigest
        """
        self.distribution = dist

    def get_max(self):
        """
        Get the maximum value in the distribution.

        @return: Maximum value
        """
        try:
            max_val = self.distribution.percentile(100)
        except ValueError:
            max_val = None
        return max_val

    def get_min(self):
        """
        Get the minimum value in the distribution.

        @return: minimum value
        """
        try:
            min_val = self.distribution.percentile(0)
        except ValueError:
            min_val = None
        return min_val

    def get_mean(self):
        """
        Get the mean of the values in the distribution.

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
        """
        Get the sum of the values in the distribution.

        @return: sum of value
        """
        centroids = self.distribution.centroids_to_list()
        return sum(c['c'] * c['m'] for c in centroids)

    def get_value(self, quantile):
        """
        Get the value of given quantile.

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
        """
        Get the size of snapshot.

        @return: Size of snapshot.
        """
        return self.distribution.n

    def get_count(self):
        """
        Get the number of values in the distribution.

        @return: Number of values
        """
        return self.get_size()


class Distribution(object):
    """
    Representation of a histogram distribution.

    Containing a timestamp and a list of centroids.
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, timestamp, centroids):
        """
        Construct a distribution.

        @param timestamp: Timestamp in milliseconds since the epoch.
        @type timestamp: long
        @param centroids: Centroids
        @type centroids: list of tuple
        """
        self.timestamp = timestamp
        self.centroids = centroids


class MinuteBin(object):
    """Representation of a bin that holds histogram for a certain minute."""

    # pylint: disable=too-few-public-methods
    def __init__(self, accuracy=100, minute_millis=None):
        """
        Construct the Minute Bin.

        @param accuracy: Accuracy range from [0, 100]
        @type accuracy: int
        @param minute_millis: The timestamp at the start of the minute.
        @type minute_millis: long
        """
        self.distribution = TDigest(delta=1 / accuracy)
        self.minute_millis = minute_millis


class List(list):
    """Wrapper of list for weakref."""

    pass


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
        """
        Construct Wavefront Histogram.

        @param clock_millis: A function which returns timestamp.
        @type clock_millis: function
        """
        self._clock_millis = clock_millis or self.current_clock_millis
        self._global_histogram_bins_list = []
        self._lock = threading.Lock()
        self._thread_local = threading.local()
        self.init_thread()

    def init_thread(self):
        self._thread_local.shared_bins_instance = List([])

        # ThreadLocal histogramBinsList where the initial value set is also
        # added to a global list of thread local histogramBinsList wrapped
        # in WeakReference.
        self._thread_local.histogram_bins_list = self._thread_local.\
            shared_bins_instance

        # Global list of thread local histogram_bins_list wrapped in
        # WeakReference.
        self._global_histogram_bins_list. \
            append(weakref.ref(self._thread_local.histogram_bins_list))

    @staticmethod
    def current_clock_millis():
        """Get current time in millisecond."""
        return time.time() * 1000

    def current_minute_millis(self):
        """Get the timestamp of start of certain minute."""
        return int(self._clock_millis() / 60000) * 60000

    def update(self, value):
        """
        Add one value to the distribution.

        @param value: value to add.
        @type value: float
        """
        try:
            self._thread_local.histogram_bins_list
        except AttributeError:
            self.init_thread()
        self.get_current_bin().distribution.update(value)

    def bulk_update(self, means, counts):
        """
        Bulk-update this histogram with a set of centroids.

        @param means: the centroid values
        @type means: list of float
        @param counts: the centroid weights/sample counts
        @type counts: list of int
        """
        try:
            self._thread_local.histogram_bins_list
        except AttributeError:
            self.init_thread()
        if means and counts:
            current_bin = self.get_current_bin()
            for i in range(min(len(means), len(counts))):
                current_bin.distribution.update(means[i], counts[i])

    def get_current_bin(self):
        """
        Retrieve the current bin.

        Will be invoked on the thread local histogram_bins_list.
        @return: Current minute bin
        @rtype: MinuteBin
        """
        try:
            self._thread_local.histogram_bins_list
        except AttributeError:
            self.init_thread()
        shared_bins_instance = self._thread_local.histogram_bins_list
        curr_minute_millis = self.current_minute_millis()

        with self._lock:
            if not shared_bins_instance or \
                    shared_bins_instance[-1].minute_millis \
                    != curr_minute_millis:
                shared_bins_instance.append(MinuteBin(self._ACCURACY,
                                                      curr_minute_millis))
            if len(shared_bins_instance) > self._MAX_BINS:
                del shared_bins_instance[0]
            return shared_bins_instance[-1]

    @staticmethod
    def std_dev():
        """Not supported. Return None."""
        return None

    def clear_prior_current_minute_bin(self, cutoff_millis):
        """
        Clear the minute bin of which timestamps if before cutoff millis.

        @param cutoff_millis: Timestamp of cutoff millis.
        @type cutoff_millis: long
        """
        for shared_bins_instance in self._global_histogram_bins_list:
            with self._lock:
                shared_bins_instance = shared_bins_instance()
                shared_bins_instance[:] = [
                    cur_bin for cur_bin in shared_bins_instance
                    if cur_bin.minute_millis > cutoff_millis]

    def flush_distributions(self):
        """
        Aggregate all the minute bins prior to the current minute.

        Only aggregating before current minute is because threads might be
        updating the current minute bin while the method is invoked.

        Returns a list of the distributions held within each bin.

        Note that invoking this method will also clear all data from the
        aggregated bins, thereby changing the state of the system and
        preventing data from being flushed more than once.

        @return: list of the distributions held within each bin
        @rtype: list of Distribution
        """
        cutoff_millis = self.current_minute_millis()

        self._global_histogram_bins_list[:] = \
            [shared_bins_instance for shared_bins_instance
             in self._global_histogram_bins_list if shared_bins_instance()]

        minute_bins = []
        for shared_bins_instance in self._global_histogram_bins_list:
            minute_bins.extend([min_bin for min_bin in shared_bins_instance()
                                if min_bin.minute_millis < cutoff_millis])

        distributions = []
        for minute_bin in minute_bins:
            centroids = [(centroid['m'], centroid['c']) for centroid
                         in minute_bin.distribution.centroids_to_list()]
            distributions.append(
                Distribution(minute_bin.minute_millis, centroids))
        self.clear_prior_current_minute_bin(cutoff_millis)
        return distributions

    def get_count(self):
        """Get the number of values in the distribution."""
        count = 0
        for shared_bins_instance in self._global_histogram_bins_list:
            count += sum(b.distribution.n for b in shared_bins_instance())
        return count

    def get_sum(self):
        """Get the sum of the values in the distribution."""
        res = 0
        for shared_bins_instance in self._global_histogram_bins_list:
            for one_bin in shared_bins_instance():
                res += sum(c['c'] * c['m'] for c
                           in one_bin.distribution.centroids_to_list())
        return res

    def get_snapshot(self):
        """
        Return a statistical of the histogram distribution.

        @return: Snapshot of Histogram
        @rtype: Snapshot
        """
        snapshot = TDigest(1 / self._ACCURACY)
        for shared_bins_instance in self._global_histogram_bins_list:
            for min_bin in shared_bins_instance():
                snapshot = snapshot + min_bin.distribution
        return Snapshot(snapshot)

    def get_max(self):
        """
        Get the maximum value in the distribution.

        Return None if the distribution is empty.
        """
        max_val = float('NaN')
        for shared_bins_instance in self._global_histogram_bins_list:
            if shared_bins_instance():
                max_val = max(max(b.distribution.percentile(100)
                                  for b in shared_bins_instance()), max_val)
        return max_val if max_val == max_val else None

    def get_min(self):
        """
        Get the minimum value in the distribution.

        Return None if the distribution is empty.
        """
        min_val = float('NaN')
        for shared_bins_instance in self._global_histogram_bins_list:
            if shared_bins_instance():
                min_val = min(min(b.distribution.percentile(0)
                                  for b in shared_bins_instance()), min_val)
        return min_val if min_val == min_val else None

    def get_mean(self):
        """
        Get the mean of the values in the distribution.

        Return None if the distribution is empty.
        """
        count = total = 0
        for shared_bins_instance in self._global_histogram_bins_list:
            for one_bin in shared_bins_instance():
                centroids = one_bin.distribution.centroids_to_list()
                count += sum(c['c'] for c in centroids)
                total += sum(c['c'] * c['m'] for c in centroids)
        if count == 0:
            return None
        return total / count
