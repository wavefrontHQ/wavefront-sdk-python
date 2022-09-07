"""All Python-sdk constants.

@author Hao Song (songhao@vmware.com).
"""

# Use this format to send metric data to Wavefront.
WAVEFRONT_METRIC_FORMAT = 'wavefront'

# Use this format to send histogram data to Wavefront.
WAVEFRONT_HISTOGRAM_FORMAT = 'histogram'

# Use this format to send tracing data to Wavefront.
WAVEFRONT_TRACING_SPAN_FORMAT = 'trace'

# GREEK LETTER DELTA.
DELTA_PREFIX = '\u2206'

# GREEK CAPITAL LETTER DELTA.
DELTA_PREFIX_2 = '\u0394'

# Heartbeat metric.
HEART_BEAT_METRIC = '~component.heartbeat'

# Internal source used for internal and aggregated metrics.
WAVEFRONT_PROVIDED_SOURCE = 'wavefront-provided'

# Null value emitted for optional undefined tags.
NULL_TAG_VAL = 'none'

# Key for defining a source.
SOURCE_KEY = 'source'

# Tag key for defining an application.
APPLICATION_TAG_KEY = 'application'

# Tag key for defining a cluster.
CLUSTER_TAG_KEY = 'cluster'

# Tag key for defining a shard.
SHARD_TAG_KEY = 'shard'

# Tag key  for defining a service.
SERVICE_TAG_KEY = 'service'

# Tag key for defining a component.
COMPONENT_TAG_KEY = 'component'

# Heart beat interval.
HEART_BEAT_INTERVAL = 10

# Name prefix for internal diagnostic metrics for Wavefront SDKs.
SDK_METRIC_PREFIX = '~sdk.python'

# Tag key for span logs.
SPAN_LOG_KEY = "_spanLogs"

# Distribution name for sdk
WAVEFRONT_SDK_PYTHON = 'wavefront-sdk-python'

# Default http status code for sending points
NO_HTTP_RESPONSE = -1
