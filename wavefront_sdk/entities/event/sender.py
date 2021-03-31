"""Events Entities.

@author Yogesh Prasad Kurmi (ykurmi@vmware.com)
"""


# pylint: disable=E0012,R0205
class WavefrontEventSender(object):
    """Interface of Event Sender for both clients."""

    # pylint: disable=too-many-arguments
    def send_event(self, name, start_time, end_time, source,
                   tags, annotations):
        """Send Event Data.

        Wavefront Event Data format
        {"name": <Event Name>, "annotations": <Annotations>,
         "hosts": <Host List>,"startTime": <Start Time>,
          "endTime": <End Time>, "tags": <Tags>}
        Example: {"name": event_via_direct_ingestion, "annotations": {
        "severity": "severe", "type": "backup", "details": "broker backup"},
         "hosts": ["localhost"], "startTime": 1590678089,
          "endTime": 1590679089, "tags": ["env:", "test"]}

        @param name: Event Name
        @type name: str
        @param start_time: Event Start Time
        @type start_time: long
        @param end_time: Event End Time
        @type end_time: long
        @param source: Source
        @type source: str
        @param tags: Tags
        @type tags: list[str]
        @param annotations: Annotations
        @type annotations: dict
        """
        raise NotImplementedError

    def send_event_now(self, events):
        """Send a list of events immediately.

        @param events: List of string events data
        @type events: list[str]
        """
        raise NotImplementedError
