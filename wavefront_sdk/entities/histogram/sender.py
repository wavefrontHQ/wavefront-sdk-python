"""Interface of Histogram Sender for both clients.

@author Hao Song (songhao@vmware.com)
"""


# pylint: disable=E0012,R0205
class WavefrontHistogramSender(object):
    """Interface of Histogram Sender for both clients."""

    # pylint: disable=too-many-arguments
    def send_distribution(self, name, centroids, histogram_granularities,
                          timestamp, source, tags):
        """Send Distribution Data.

        Wavefront Histogram Data format
        {!M | !H | !D} [<timestamp>] #<count> <mean> [centroids]
        <histogramName> source=<source> [pointTags]
        Example: "!M 1533531013 #20 30.0 #10 5.1 request.latency
                  source=appServer1 region=us-west"

        @param name: Histogram Name
        @type name: str
        @param centroids: List of centroids(pairs)
        @type centroids: list
        @param histogram_granularities: Histogram Granularities
        @type histogram_granularities: set
        @param timestamp: Timestamp
        @type timestamp: long
        @param source: Source
        @type source: str
        @param tags: Tags
        @type tags: dict
        """
        raise NotImplementedError

    def send_formatted_metric(self, distribution):
        """Send a formatted histogram immediately.

        @param distribution: Formatted distribution
        @type: str
        """
        self.send_distribution_now([distribution])

    def send_distribution_now(self, distributions):
        """Send a list of distributions immediately.

        Have to construct the data manually by calling
        common.utils.histogram_to_line_data()

        @param distributions: List of string distribution data
        @type distributions: list[str]
        """
        raise NotImplementedError
