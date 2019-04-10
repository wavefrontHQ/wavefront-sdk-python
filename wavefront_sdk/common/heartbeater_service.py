"""Service that periodically reports component heartbeats to Wavefront.

@author Hao Song (songhao@vmware.com).
"""

import logging
import threading
import time

from .constants import APPLICATION_TAG_KEY
from .constants import CLUSTER_TAG_KEY
from .constants import COMPONENT_TAG_KEY
from .constants import HEART_BEAT_METRIC
from .constants import NULL_TAG_VAL
from .constants import SERVICE_TAG_KEY
from .constants import SHARD_TAG_KEY

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


# pylint: disable=E0012,R0205
# pylint: disable=too-few-public-methods
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
        if isinstance(components, str):
            components = [components]
        for component in components:
            self.heartbeat_metric_tags_list.append(
                {
                    APPLICATION_TAG_KEY: application_tags.application,
                    CLUSTER_TAG_KEY: application_tags.cluster or NULL_TAG_VAL,
                    SERVICE_TAG_KEY: application_tags.service,
                    SHARD_TAG_KEY: application_tags.shard or NULL_TAG_VAL,
                    COMPONENT_TAG_KEY: component
                }
            )
        self._closed = False
        self._timer = None
        self._run()

    def _schedule_timer(self):
        self._timer = threading.Timer(self.reporting_interval_seconds,
                                      self._run)
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
        # pylint: disable=broad-except,fixme
        # TODO: Please make sure we catch more specific exception here.
        except Exception:
            LOGGER.warning('Can not report %s to wavefront', HEART_BEAT_METRIC)

    def close(self):
        """Cancel the timer."""
        self._closed = True
        if self._timer is not None:
            self._timer.cancel()
