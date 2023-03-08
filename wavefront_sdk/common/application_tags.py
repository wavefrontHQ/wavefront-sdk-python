"""Metadata about your application represented as tags in Wavefront.

@author: Hao Song (songhao@vmware.com)
"""
import os
import re

from .constants import APPLICATION_TAG_KEY
from .constants import CLUSTER_TAG_KEY
from .constants import NULL_TAG_VAL
from .constants import SERVICE_TAG_KEY
from .constants import SHARD_TAG_KEY


# pylint: disable=E0012,R0205
class ApplicationTags(object):
    """Metadata about your application represented as tags in Wavefront."""

    # pylint: disable=too-many-arguments
    def __init__(self, application, service, cluster=None, shard=None,
                 custom_tags=None):
        """Construct ApplicationTags.

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
        self._custom_tags = []
        if custom_tags:
            self._custom_tags.extend(custom_tags)

    @property
    def application(self):
        """Get Application Name."""
        return self._application

    @property
    def service(self):
        """Get Service Name."""
        return self._service

    @property
    def cluster(self):
        """Get Cluster Name."""
        return self._cluster

    @property
    def shard(self):
        """Get Shard Name."""
        return self._shard

    @property
    def custom_tags(self):
        """Get Custom Tags."""
        return self._custom_tags

    def get_as_list(self):
        """Get all tags as a list."""
        tags = [(APPLICATION_TAG_KEY, self.application),
                (SERVICE_TAG_KEY, self.service),
                (CLUSTER_TAG_KEY, self.cluster or NULL_TAG_VAL),
                (SHARD_TAG_KEY, self.shard or NULL_TAG_VAL)]
        if self.custom_tags:
            tags.extend(self.custom_tags)
        return tags

    def add_custom_tags_from_env(self, pattern):
        """Set custom tags from environment variables.

        (that match the regex pattern)
        @param pattern: Regex pattern
        """
        for key in os.environ:
            if re.match(pattern, key, re.IGNORECASE):
                value = os.environ[key]
                if value:
                    self._custom_tags.append((key, value))

    def add_custom_tag_from_env(self, tag_key, var_key):
        """Set a custom tag from the given environment variable.

        @param tag_key: Key of the custom tag
        @param var_name: Key of the environment variable
        """
        # pylint: disable=broad-exception-raised
        if var_key in os.environ:
            value = os.environ[var_key]
            if value:
                self._custom_tags.append((tag_key, value))
        else:
            raise Exception("var_key is an invalid environment variable.")
