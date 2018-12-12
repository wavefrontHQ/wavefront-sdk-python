"""
Service that periodically reports component heartbeats to Wavefront.

@author Hao Song (songhao@vmware.com).
"""

import time
import logging
from threading import Timer
from wavefront_sdk.common.constants import HEART_BEAT_METRIC, \
    APPLICATION_TAG_KEY, CLUSTER_TAG_KEY, SERVICE_TAG_KEY, SHARD_TAG_KEY, \
    COMPONENT_TAG_KEY, NULL_TAG_VAL

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class HeartbeaterService(object):
    """Service that periodically reports component heartbeats to Wavefront."""

    # pylint: disable=too-many-arguments
    def __init__(self, wavefront_client, application_tags, component, source,
                 reporting_interval_seconds):
        """
        Construct HeartbeaterService.
        @param wavefront_client: Wavefront Proxy or Direct Ingestion client.
        @param application_tags: ApplicationTags.
        @param component: Component.
        @param source: Source.
        @param reporting_interval_seconds: Interval of reporting heart beat.
        """
        self.wavefront_client = wavefront_client
        self.application_tags = application_tags
        self.source = source
        self.reporting_interval_seconds = reporting_interval_seconds
        self.heartbeat_metric_tags = {
            APPLICATION_TAG_KEY: application_tags.application,
            CLUSTER_TAG_KEY: application_tags.cluster or NULL_TAG_VAL,
            SERVICE_TAG_KEY: application_tags.service,
            SHARD_TAG_KEY: application_tags.shard or NULL_TAG_VAL,
            COMPONENT_TAG_KEY: component
        }
        self._timer = None
        self._schedule_timer()

    def _schedule_timer(self):
        self._timer = Timer(self.reporting_interval_seconds, self._run)
        self._timer.start()

    def _run(self):
        try:
            self._report()
        finally:
            self._schedule_timer()

    def _report(self):
        try:
            self.wavefront_client.send_metric(HEART_BEAT_METRIC, 1.0,
                                              time.time(), self.source,
                                              self.heartbeat_metric_tags)
        except Exception:
            LOGGER.warning('Can not report %s to wavefront', HEART_BEAT_METRIC)
