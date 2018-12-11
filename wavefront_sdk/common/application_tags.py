"""
Metadata about your application represented as tags in Wavefront.

@author: Hao Song (songhao@vmware.com)
"""

from wavefront_sdk.common.constants import APPLICATION_TAG_KEY, \
    SERVICE_TAG_KEY, CLUSTER_TAG_KEY, SHARD_TAG_KEY, NULL_TAG_VAL


class ApplicationTags:
    """Metadata about your application represented as tags in Wavefront."""

    def __init__(self, application, service, cluster=None, shard=None,
                 custom_tags=None):
        """
        Construct ApplicationTags.

        @param application: Application Name
        @param service: Service Name
        @param cluster: Cluster Name
        @param shard: Shard Name
        @param custom_tags: List of pairs of custom tags
        """
        if not application:
            raise AttributeError('Missing "application" parameter in '
                                 'ApplicationTags!')
        if not service:
            raise AttributeError('Missing "service" parameter in '
                                 'ApplicationTags!')
        self._application = application
        self._service = service
        self._cluster = cluster
        self._shard = shard
        self._custom_tags = custom_tags

    @property
    def application(self):
        return self._application

    @property
    def service(self):
        return self._service

    @property
    def cluster(self):
        return self._cluster

    @property
    def shard(self):
        return self._shard

    @property
    def custom_tags(self):
        return self._custom_tags

    def get_as_list(self):
        tags = [(APPLICATION_TAG_KEY, self.application),
                (SERVICE_TAG_KEY, self.service),
                (CLUSTER_TAG_KEY, self.cluster or NULL_TAG_VAL),
                (SHARD_TAG_KEY, self.shard or NULL_TAG_VAL)]
        tags.extend(self.custom_tags)
        return tags
