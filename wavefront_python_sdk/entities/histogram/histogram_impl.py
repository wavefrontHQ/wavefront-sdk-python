from __future__ import division
from tdigest import TDigest
import threading
import weakref
import time


class Snapshot(object):
    def __init__(self, dist):
        """

        @param dist:
        @type dist: TDigest
        """
        self.distribution = dist

    def get_max(self):
        # TO-DO: Is this equivalent to Java TDigest.getMax()
        try:
            max_val = self.distribution.percentile(100)
        except ValueError:
            max_val = None
        return max_val

    def get_min(self):
        # TO-DO: Is this equivalent to Java TDigest.getMin()
        try:
            min_val = self.distribution.percentile(0)
        except ValueError:
            min_val = None
        return min_val

    def get_mean(self):
        # try:
        #     return self.distribution.trimmed_mean(0, 100)
        # except ZeroDivisionError:
        #     return None
        centroids = self.distribution.centroids_to_list()
        if not centroids:
            return None
        return sum(c['c'] * c['m'] for c in centroids) / sum(c['c'] for c in
                                                             centroids)

    def get_sum(self):
        centroids = self.distribution.centroids_to_list()
        return sum(c['c'] * c['m'] for c in centroids)

    def get_value(self, quantile):
        """

        @param quantile: Quantile, range from 0 to 1
        @type quantile: float
        @return:
        """
        percentile = quantile * 100
        try:
            return self.distribution.percentile(percentile)
        except ValueError:
            # ValueError("Tree is empty") from TDigest
            return None

    def get_size(self):
        return self.distribution.n

    def get_count(self):
        # TODO: What's the difference between getSize and getCount in Java.
        return self.get_size()
        # return len(self.distribution)


class Distribution(object):
    def __init__(self, timestamp, centroids):
        """

        @param timestamp:
        @type timestamp: long
        @param centroids:
        @type centroids: list of tuple
        """
        self.timestamp = timestamp
        self.centroids = centroids


class MinuteBin(object):
    def __init__(self, accuracy=100, minute_millis=None):
        """

        @param accuracy:
        @type accuracy: int
        @param minute_millis:
        @type minute_millis: long
        """
        self.distribution = TDigest(delta=1 / accuracy)
        self.minute_millis = minute_millis


class List(list):
    pass


class WavefrontHistogramImpl(object):
    _ACCURACY = 100  # Accuracy = Compression = 1 / Delta
    _MAX_BINS = 10

    def __init__(self, clock_millis=None):
        """

        @param clock_millis:
        @type clock_millis: function
        """
        self._clock_millis = clock_millis or self.current_clock_millis
        self._global_histogram_bins_list = []
        self._lock = threading.Lock()
        self._thread_local = threading.local()
        self._shared_bins_instance = List([])
        self._thread_local.histogram_bins_list = self._shared_bins_instance
        self._global_histogram_bins_list. \
            append(weakref.ref(self._shared_bins_instance))

    def test(self):
        print(self._shared_bins_instance)
        print(self._thread_local.histogram_bins_list)
        print(self._global_histogram_bins_list[0]())
        print(len(self._global_histogram_bins_list))

    def test_update(self):
        self._shared_bins_instance.append(1)
        self._thread_local.histogram_bins_list.append(2)

    @staticmethod
    def current_clock_millis():
        return time.time() * 1000

    def current_minute_millis(self):
        return int(self._clock_millis() / 60000) * 60000

    def update(self, value):
        """

        @param value:
        @type value: float
        """
        self.get_current_bin().distribution.update(value)

    def bulk_update(self, means, counts):
        """

        @param means: the centroid values
        @type means: list of float
        @param counts: the centroid weights/sample counts
        @type counts: list of int
        @return:
        """
        if means and counts:
            n = min(len(means), len(counts))
            current_bin = self.get_current_bin()
            for i in range(n):
                current_bin.distribution.update(means[i], counts[i])

    def get_current_bin(self):
        """
        Retrieve the current bin.

        Will be invoked on the thread local histogram_bins_list
        @return: Current minute bin
        @rtype: MinuteBin
        """
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

        @param cutoff_millis:
        @type cutoff_millis: long
        @return:
        """
        for shared_bins_instance in self._global_histogram_bins_list:
            with self._lock:
                shared_bins_instance = shared_bins_instance()
                shared_bins_instance[:] = [
                    cur_bin for cur_bin in shared_bins_instance
                    if cur_bin.minute_millis > cutoff_millis]

    def flush_distributions(self):
        """

        @return:
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
        count = 0
        for shared_bins_instance in self._global_histogram_bins_list:
            count += sum(b.distribution.n for b in shared_bins_instance())
        return count

    def get_sum(self):
        res = 0
        for shared_bins_instance in self._global_histogram_bins_list:
            for one_bin in shared_bins_instance():
                res += sum(c['c'] * c['m'] for c
                           in one_bin.distribution.centroids_to_list())
        return res

    def get_snapshot(self):
        snapshot = TDigest(1 / self._ACCURACY)
        for shared_bins_instance in self._global_histogram_bins_list:
            for min_bin in shared_bins_instance():
                snapshot = snapshot + min_bin.distribution
        return Snapshot(snapshot)

    def get_max(self):
        max_val = float('NaN')
        for shared_bins_instance in self._global_histogram_bins_list:
            if shared_bins_instance():
                max_val = max(max(b.distribution.percentile(100)
                                  for b in shared_bins_instance()), max_val)
        return max_val if max_val == max_val else None

    def get_min(self):
        min_val = float('NaN')
        for shared_bins_instance in self._global_histogram_bins_list:
            if shared_bins_instance():
                min_val = min(min(b.distribution.percentile(0)
                                  for b in shared_bins_instance()), min_val)
        return min_val if min_val == min_val else None

    def get_mean(self):
        count = total = 0
        for shared_bins_instance in self._global_histogram_bins_list:
            for one_bin in shared_bins_instance():
                centroids = one_bin.distribution.centroids_to_list()
                count += sum(c['c'] for c in centroids)
                total += sum(c['c'] * c['m'] for c in centroids)
        if count == 0:
            return None
        return total / count


if __name__ == "__main__":
    histogram = WavefrontHistogramImpl()
    histogram.test()
    histogram.test_update()
    histogram.test()
    histogram.flush_distributions()
