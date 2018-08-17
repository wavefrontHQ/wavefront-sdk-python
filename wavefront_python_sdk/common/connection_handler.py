from wavefront_python_sdk.common import utils


class ConnectionHandler(object):
    """
    A connection handler for both proxy and direct client.
    Handle the failure atomic counter.
    And provide connect function to be override by clients.
    """

    def __init__(self):
        self._failure = utils.AtomicCounter()

    def connect(self):
        pass

    def get_failure_count(self):
        """
        Get failure count for one connection
        @return: failure count
        """
        return self._failure.value

    def increment_failure_count(self):
        """
        Increment failure count by one
        """
        self._failure.increment()
