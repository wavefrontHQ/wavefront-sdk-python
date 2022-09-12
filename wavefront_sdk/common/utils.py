"""
Utils module contains useful function for preparing and processing data.

@author: Hao Song (songhao@vmware.com)
"""

import gzip
import io
import json
import logging
import re
import threading

import pkg_resources

from wavefront_sdk.common.constants import SPAN_LOG_KEY

LOGGER = logging.getLogger('wavefront_sdk.utils')


# pylint: disable=E0012,R0205
class AtomicCounter(object):
    """An atomic, thread-safe incrementing counter."""

    def __init__(self, initial=0):
        """Construct Atomic Counter.

        @param initial: Initial value of the counter
        """
        self.value = initial
        self._lock = threading.RLock()

    def increment(self, num=1):
        """Increment atomic counter value.

        @param num: Num to be increased, 1 by default
        @return: Current value after increment
        """
        with self._lock:
            self.value += num
            return self.value

    def get(self):
        """Get current atomic counter value.

        @return: Current atomic counter value.
        @rtype: float or int
        """
        return self.value


class HashableDict(dict):
    """Hashable Dict."""

    def __hash__(self):
        """Hash of the dict."""
        return hash(tuple(sorted(self.items())))


def chunks(data_list, batch_size):
    """Split list of data into chunks with fixed batch size.

    @param data_list: List of data
    @param batch_size: Batch size of each chunk
    @return: Return a lazy generator object for iteration
    """
    for i in range(0, len(data_list), batch_size):
        yield data_list[i:i + batch_size]


def gzip_compress(data, compresslevel=9):
    """Compress data using GZIP.

    @param data: Data to compress
    @param compresslevel: Compress Level
    @return: Compressed data
    """
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='wb',
                       compresslevel=compresslevel) as gzip_file:
        gzip_file.write(data)
    return buf.getvalue()


def sanitize(string):
    """Sanitize a string with quotes.

    @param string: Input string
    @return: Sanitized string
    """
    return sanitize_internal(string, True)


def sanitize_without_quotes(string):
    """Sanitize a string without quotes.

    @param string: Input string
    @return: Sanitized string
    """
    return sanitize_internal(string, False)


def sanitize_value(string):
    """Sanitize string of tags value and source.

    @oaram string: Input String
    @return: Sanitized String
    """
    res = string.strip()
    res = res.replace("\"", "\\\"")
    return "\"" + res.replace("\n", "\\n") + "\""


def sanitize_internal(string, add_quotes):
    """Sanitize string of metric name, key of tags.

    @param string: Input string
    @add_quotes: Add quotes or not
    @return: Sanitized String
    """
    builder = ''
    if add_quotes:
        builder += '"'
    for i, char in enumerate(string):
        is_legal = True
        is_tilda_prefixed = ord(string[0]) == 126
        is_delta_prefixed = ord(string[0]) == 0x2206 or ord(
            string[0]) == 0x0394
        is_delta_tilda_prefixed = is_delta_prefixed and ord(string[1]) == 126
        cur = ord(char)
        if not (44 <= cur <= 46) and not (48 <= cur <= 57) \
                and not (65 <= cur <= 90) and not \
                (97 <= cur <= 122) and not cur == 95:
            # legal characters are any single character
            # between , (index 44) and . (index 46) or
            # between 0 (index 48) and 9 (index 57) or
            # between A (index 65) and Z (index 90) or
            # between a (index 97) and z (index 122) or
            # _ (index 95)
            if not ((i == 0 and (is_delta_prefixed or is_tilda_prefixed)) or
                    (i == 1 and is_delta_tilda_prefixed)):
                is_legal = False
            # first character can also be \u2206 (∆ - INCREMENT) or
            # \u0394 (Δ - GREEK CAPITAL LETTER DELTA) or
            # ~ tilda character for internal metrics
            # second character can be ~ tilda character if first character
            # is \u2206 (∆ - INCREMENT) or \u0394 (Δ - GREEK CAPITAL LETTER)
        builder += char if is_legal else '-'
    if add_quotes:
        builder += '"'
    return builder


def is_blank(string):
    """
    Check is a string is black or not, either none or only contains whitespace.

    @param string: String to be checked
    @return: Is blank or not
    """
    return string is None or len(string) == 0 or string.isspace()
    # return len(re.sub(r'[\s]+', '', s)) == 0


def validate_tags(tags):
    """
    Ensure that the tag is not empty, otherwise throw the error.

    :param tags:
    :return:
    """
    for tag in tags:
        if is_blank(tag):
            raise ValueError('Event tag cannot be blank')


def validate_annotations(annotations):
    """
    Ensure that annotation key and value are not empty.

    Otherwise throw the error.

    :param annotations:
    :return:
    """
    for key, value in annotations.items():
        if is_blank(key):
            raise ValueError('Annotation key cannot be blank')
        if is_blank(value):
            raise ValueError('Annotation value cannot be blank for key: '
                             + key)


# pylint: disable=too-many-arguments

def metric_to_line_data(name, value, timestamp, source, tags, default_source):
    """Metric Data to String.

    Wavefront Metrics Data format
    <metricName> <metricValue> [<timestamp>] source=<source> [pointTags]
    Example: "new-york.power.usage 42422 1533531013 source=localhost
              datacenter=dc1"

    @param name: Metric Name
    @type name: str
    @param value: Metric Value
    @type value: float
    @param timestamp: Timestamp
    @type timestamp: long
    @param source: Source
    @type source: str
    @param tags: Tags
    @type tags: dict
    @param default_source:
    @type default_source: str
    @return: String
    """
    if is_blank(name):
        raise ValueError('Metrics name cannot be blank')

    if is_blank(source):
        source = default_source

    str_builder = [sanitize(name), str(float(value))]
    if timestamp is not None:
        str_builder.append(str(int(timestamp)))
    str_builder.append('source=' + sanitize_value(source))
    if tags is not None:
        for key, val in tags.items():
            if is_blank(key):
                raise ValueError('Metric point tag key cannot be blank')
            if is_blank(val):
                raise ValueError('Metric point tag value cannot be blank')
            str_builder.append(sanitize(key) + '=' + sanitize_value(val))
    return ' '.join(str_builder) + '\n'


def histogram_to_line_data(name, centroids, histogram_granularities, timestamp,
                           source, tags, default_source):
    """Wavefront Histogram Data format.

    {!M | !H | !D} [<timestamp>] #<count> <mean> [centroids] <histogramName>
    source=<source> [pointTags]
    Example: "!M 1533531013 #20 30.0 #10 5.1 request.latency source=appServer1
              region=us-west"

    @param name: Histogram Name
    @type name: str
    @param centroids: List of centroids(pairs)
    @type centroids: list
    @param histogram_granularities: Histogram Granularities
    @type histogram_granularities: set
    @param timestamp: Timestamp
    @type timestamp: long
    @param source: Source
    @type source: str
    @param tags: Tags
    @type tags: dict
    @param default_source: Default Source
    @type default_source: str
    @return: String data of Histogram
    """
    if is_blank(name):
        raise ValueError('Histogram name cannot be blank')

    if not histogram_granularities:
        raise ValueError('Histogram granularities cannot be null or empty')

    if not centroids:
        raise ValueError('A distribution should have at least one centroid')

    if is_blank(source):
        source = default_source

    line_builder = []
    for histogram_granularity in histogram_granularities:
        str_builder = [histogram_granularity]
        if timestamp is not None:
            str_builder.append(str(int(timestamp)))
        for centroid_1, centroid_2 in centroids:
            str_builder.append('#' + str(centroid_2))
            str_builder.append(str(centroid_1))
        str_builder.append(sanitize(name))
        str_builder.append('source=' + sanitize_value(source))
        if tags is not None:
            for key in tags:
                if is_blank(key):
                    raise ValueError('Histogram tag key cannot be blank')
                if is_blank(tags[key]):
                    raise ValueError('Histogram tag value cannot be blank')
                str_builder.append(
                    sanitize(key) + '=' + sanitize_value(tags[key]))
        line_builder.append(' '.join(str_builder))
    return '\n'.join(line_builder) + '\n'


# pylint: disable=unused-argument
def tracing_span_to_line_data(name, start_millis, duration_millis, source,
                              trace_id, span_id, parents, follows_from, tags,
                              span_logs, default_source):
    """Wavefront Tracing Span Data format.

    <tracingSpanName> source=<source> [pointTags] <start_millis>
    <duration_milli_seconds>
    Example: "getAllUsers source=localhost
              traceId=7b3bf470-9456-11e8-9eb6-529269fb1459
              spanId=0313bafe-9457-11e8-9eb6-529269fb1459
              parent=2f64e538-9457-11e8-9eb6-529269fb1459
              application=Wavefront http.method=GET
              1533531013 343500"

    @param name: Span Name
    @type name: str
    @param start_millis: Start time
    @type start_millis: long
    @param duration_millis: Duration time
    @type duration_millis: long
    @param source: Source
    @type source: str
    @param trace_id: Trace ID
    @type trace_id: UUID
    @param span_id: Span ID
    @type span_id: UUID
    @param parents: Parents Span ID
    @type parents: List of UUID
    @param follows_from: Follows Span ID
    @type follows_from: List of UUID
    @param tags: Tags
    @type tags: list
    @param span_logs: Span Log
    @param default_source: Default Source
    @type default_source: str
    @return: String data of tracing span
    """
    # pylint: disable=too-many-locals
    if is_blank(name):
        raise ValueError('Span name cannot be blank')

    if is_blank(source):
        source = default_source

    str_builder = [sanitize_value(name),
                   'source=' + sanitize_value(source),
                   'traceId=' + str(trace_id),
                   'spanId=' + str(span_id)]
    if parents is not None:
        for uuid in parents:
            str_builder.append('parent=' + str(uuid))
    if follows_from is not None:
        for uuid in follows_from:
            str_builder.append('followsFrom=' + str(uuid))
    if span_logs:
        tags.append((SPAN_LOG_KEY, 'true'))
    if tags is not None:
        tag_set = set()
        for key, val in tags:
            if is_blank(key):
                raise ValueError('Span tag key cannot be blank')
            if is_blank(val):
                raise ValueError('Span tag val cannot be blank')
            cur_tag = sanitize(key) + '=' + sanitize_value(val)
            if cur_tag not in tag_set:
                str_builder.append(cur_tag)
                tag_set.add(cur_tag)
    str_builder.append(str(start_millis))
    str_builder.append(str(duration_millis))
    return ' '.join(str_builder) + '\n'


def span_log_to_line_data(trace_id, span_id, span_logs, span, scrambler=None):
    """Wavefront Tracing Span Log JSON format.

    @param trace_id: Trace ID
    @param span_id: Span ID
    @param span_logs: Span Log
    @param span: Span line
    @param scrambler: Additional UUID, optional
    @return: Span Log in JSON Format
    """
    span_log_json = {'traceId': str(trace_id),
                     'spanId': str(span_id),
                     'logs': span_logs,
                     'span': str(span)}
    if scrambler:
        span_log_json['_scrambler'] = str(scrambler)
    return json.dumps(span_log_json, default=lambda o: o.__dict__) + '\n'


# pylint: disable=too-many-branches
def event_to_json(name, start_time, end_time, source, tags,
                  annotations, default_source):
    """Wavefront Event JSON format for direct data ingestion.

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
    @param default_source: Default Host Name
    @type default_source: str
    @return: Event JSON as String
    """
    if is_blank(name):
        raise ValueError('Event name cannot be blank')

    if not start_time:
        raise ValueError('Event start time cannot be blank')

    if not source:
        source = default_source

    event = {'name': name, 'annotations': {}, 'hosts': [source]}
    event['startTime'] = start_time

    if end_time:
        event['endTime'] = end_time
    else:
        event['endTime'] = start_time + 1

    if annotations:
        validate_annotations(annotations)
        event['annotations'] = annotations

    if tags:
        validate_tags(tags)
        event['tags'] = tags

    return str(json.dumps(event))


def get_version(name):
    """Return semantic version of sdk used ex: 'v1.6.3'.

    @param name: SDK Name
    @type name: str
    @return: The version of this library. ex: 'v1.6.3' If version can't be
      found, returns 'unknown'
    """
    try:
        version = pkg_resources.require(name)[0].version
        return "v" + version
    except pkg_resources.DistributionNotFound:
        LOGGER.warning('Unable to get version info,'
                       ' No distribution found for : %s', name)
    return "unknown"


def get_sem_ver(name):
    """Return semantic version of sdk used in Wavefront reportable format.

    Ex: <major>.<2-digit-minor><2-digit-patch> (1.0603 => v1.6.3)

    @param name: SDK Name
    @type name: str
    @return: Semantic version in wavefront format as String. Ex: '1.0603'
    """
    version = get_version(name)
    if version.startswith('v'):
        return get_sem_ver_value(version[1:])
    return "0.0"


def get_sem_ver_value(version):
    """Return semantic version of sdk in Wavefront reportable format.

    Ex: <major>.<2-digit-minor><2-digit-patch> (1.0603 => v1.6.3)

    @param version: SDK Version
    @type version: str
    @return: Semantic version in wavefront format as String
    """
    for match in re.finditer(
            "([0-9]\\d*)\\.(\\d+)\\.(\\d+)(?:-([a-zA-Z0-9]+))?", version):
        major = match.group(1) + "."
        minor = match.group(2) \
            if len(match.group(2)) != 1 else "0" + match.group(2)
        patch = match.group(3) \
            if len(match.group(3)) != 1 else "0" + match.group(3)
        return major + minor + patch
    return "0.0"


def event_to_line_data(name, start_time, end_time, source, tags,
                       annotations, default_source):
    """Wavefront Event Line format for data ingestion via proxy.

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
    @param default_source: Default Host Name
    @type default_source: str
    @return: Event as String
    """
    str_builder = ['@Event']
    if is_blank(name):
        raise ValueError('Event name cannot be blank')

    if not start_time:
        raise ValueError('Event start time cannot be blank')

    str_builder.append(str(start_time))

    if end_time:
        str_builder.append(str(end_time))
    else:
        str_builder.append(str(start_time + 1))

    str_builder.append('"' + name + '"')

    if annotations:
        validate_annotations(annotations)
        for key, value in annotations.items():
            str_builder.append(key + '="' + value + '"')

    if not source:
        source = default_source

    str_builder.append('host="' + source + '"')

    if tags:
        validate_tags(tags)
        for tag in tags:
            str_builder.append('tag="' + tag + '"')

    return ' '.join(str_builder) + '\n'
