"""Service that periodically reports component heartbeats to Wavefront.

@author Hao Song (songhao@vmware.com).
"""

import logging
import threading
import time

from wavefront_sdk.common.utils import HashableDict

from .constants import APPLICATION_TAG_KEY
from .constants import CLUSTER_TAG_KEY
from .constants import COMPONENT_TAG_KEY
from .constants import HEART_BEAT_METRIC
from .constants import NULL_TAG_VAL
from .constants import SERVICE_TAG_KEY
from .constants import SHARD_TAG_KEY


# pylint: disable=E0012,R0205
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes
class HeartbeaterService(object):
    """Service that periodically reports component heartbeats to Wavefront."""

    # pylint: disable=too-many-arguments
    def __init__(self, wavefront_client, application_tags, components, source):
        """Construct HeartbeaterService.

        @param wavefront_client: Wavefront Proxy or Direct Ingestion client.
        @param application_tags: ApplicationTags.
        @param components: List of str indicates Components.
        @param source: Source.
        """
        self.wavefront_client = wavefront_client
        self.application_tags = application_tags
        self.source = source
        self.reporting_interval_seconds = 60 * 5
        self.heartbeat_metric_tags_list = []
        self.custom_tags_set = set()
        if isinstance(components, str):
            components = [components]
        for component in components:
            metric_tags = {
                APPLICATION_TAG_KEY: application_tags.application,
                CLUSTER_TAG_KEY: application_tags.cluster or NULL_TAG_VAL,
                SERVICE_TAG_KEY: application_tags.service,
                SHARD_TAG_KEY: application_tags.shard or NULL_TAG_VAL,
                COMPONENT_TAG_KEY: component
            }
            if application_tags.custom_tags:
                metric_tags.update(dict(application_tags.custom_tags))
            self.heartbeat_metric_tags_list.append(metric_tags)
        self._closed = False
        self._timer = None
        self._run()

    def report_custom_tags(self, custom_tags):
        """
        Append custom tags for heartbeat reporting.

        @param custom_tags: dict of custom tags.
        """
        self.custom_tags_set.add(HashableDict(custom_tags))

    def _schedule_timer(self):
        self._timer = threading.Timer(self.reporting_interval_seconds,
                                      self._run)
        self._timer.daemon = True
        self._timer.start()

    def _run(self):
        try:
            self._report()
        finally:
            if not self._closed:
                self._schedule_timer()

    def _report(self):
        try:
            for heartbeat in self.heartbeat_metric_tags_list:
                self.wavefront_client.send_metric(HEART_BEAT_METRIC, 1.0,
                                                  time.time(), self.source,
                                                  heartbeat)
            while self.custom_tags_set:
                self.wavefront_client.send_metric(HEART_BEAT_METRIC, 1.0,
                                                  time.time(), self.source,
                                                  self.custom_tags_set.pop())

        # pylint: disable=broad-except,fixme
        # TODO: Please make sure we catch more specific exception here.
        except Exception:
            logging.warning('Can not report %s to wavefront',
                            HEART_BEAT_METRIC)

    def close(self):
        """Cancel the timer."""
        self._closed = True
        if self._timer is not None:
            self._timer.cancel()
