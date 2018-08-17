from __future__ import absolute_import, division, print_function

from wavefront_python_sdk.common.utils import AtomicCounter


class ConnectionHandler(object):
    """
    A connection handler for both proxy and direct client.
    Handle the failure atomic counter.
    And provide connect function to be override by clients.

    @author Hao Song (songhao@vmware.com).
    """
    def __init__(self):
        self._failure = AtomicCounter()

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
