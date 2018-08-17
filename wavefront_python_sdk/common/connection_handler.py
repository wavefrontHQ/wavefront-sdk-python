from __future__ import absolute_import, division, print_function

from wavefront_python_sdk.common.utils import AtomicCounter


class ConnectionHandler:
    def __init__(self):
        self._failure = AtomicCounter()

    def connect(self):
        pass

    def get_failure_count(self):
        return self._failure.value

    def increment_failure_count(self):
        self._failure.increment()
