"""A connection handler for both proxy and direct client.

@author: Hao Song (songhao@vmware.com)
"""

from . import utils


# pylint: disable=E0012,R0205
class ConnectionHandler(object):
    """A connection handler for both proxy and direct client.

    Handle the failure atomic counter.
    """

    def __init__(self):
        """Initialize the failure atomic counter."""
        self._failure = utils.AtomicCounter()

    def get_failure_count(self):
        """Get failure count for one connection.

        @return: failure count
        """
        return self._failure.value

    def increment_failure_count(self):
        """Increment failure count by one."""
        self._failure.increment()
