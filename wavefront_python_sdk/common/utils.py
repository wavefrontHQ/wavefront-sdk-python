from __future__ import absolute_import, division, print_function

import re
import io
from gzip import GzipFile
import threading


class AtomicCounter:
    """An atomic, thread-safe incrementing counter."""

    def __init__(self, initial=0):
        self.value = initial
        self._lock = threading.Lock()

    def increment(self, num=1):
        with self._lock:
            self.value += num
            return self.value


def chunks(data_list, batch_size):
    """Yield successive batch_size chunks from l."""
    for i in range(0, len(data_list), batch_size):
        yield data_list[i:i + batch_size]


def gzip_compress(data, compresslevel=9):
    buf = io.BytesIO()
    with GzipFile(fileobj=buf, mode='wb', compresslevel=compresslevel) as f:
        f.write(data)
    return buf.getvalue()


def sanitize(s):
    whitespace_sanitized = re.sub(r"[\s]+", "-", s)
    if "\"" in whitespace_sanitized:
        return "\"" + re.sub(r"[\"]+", '\\\\\"', whitespace_sanitized) + "\""
    else:
        return "\"" + whitespace_sanitized + "\""


def is_blank(s):
    return s is None or len(s) == 0 or s.isspace()
    # return len(re.sub(r"[\s]+", "", s)) == 0


def metric_to_line_data(name, value, timestamp, source, tags, default_source):
    # Wavefront Metrics Data format
    # <metricName> <metricValue> [<timestamp>] source=<source> [pointTags]
    # Example: "new-york.power.usage 42422 1533531013 source=localhost datacenter=dc1"
    if is_blank(name):
        raise ValueError("Metrics name cannot be blank")

    if is_blank(source):
        source = default_source

    str_builder = [sanitize(name), float(value)]
    if timestamp is not None:
        str_builder.append(int(timestamp))
    str_builder.append("source=" + sanitize(source))
    if tags is not None:
        for key in tags:
            if is_blank(key):
                raise ValueError("Metric point tag key cannot be blank")
            if is_blank(tags[key]):
                raise ValueError("Metric point tag value cannot be blank")
            str_builder.append(sanitize(key) + '=' + sanitize(tags[key]))
    return ' '.join('{0}'.format(s) for s in str_builder) + "\n"


def histogram_to_line_data(name, centroids, histogram_granularities, timestamp, source, tags, default_source):
    if is_blank(name):
        raise ValueError("Histogram name cannot be blank")

    if histogram_granularities is None or len(histogram_granularities) == 0:
        raise ValueError("Histogram granularities cannot be null or empty")

    if centroids is None or len(centroids) == 0:
        raise ValueError("A distribution should have at least one centroid")

    if is_blank(source):
        source = default_source

    line_builder = []
    for histogram_granularity in histogram_granularities:
        str_builder = [histogram_granularity.identifier]
        if timestamp is not None:
            str_builder.append(int(timestamp))
        for centroid_1, centroid_2 in centroids:
            str_builder.append("#" + repr(centroid_2))
            str_builder.append(centroid_1)
        str_builder.append(sanitize(name))
        str_builder.append("source=" + sanitize(source))
        if tags is not None:
            for key in tags:
                if is_blank(key):
                    raise ValueError("Histogram tag key cannot be blank")
                if is_blank(tags[key]):
                    raise ValueError("Histogram tag value cannot be blank")
                str_builder.append(sanitize(key) + '=' + sanitize(tags[key]))
        line_builder.append(' '.join('{0}'.format(s) for s in str_builder))
    return '\n'.join('{0}'.format(line) for line in line_builder) + "\n"


def tracing_span_to_line_data(name, start_millis, duration_millis, source, trace_id, span_id,
                              parents, follows_from, tags, span_logs, default_source):
    if is_blank(name):
        raise ValueError("Span name cannot be blank")

    if is_blank(source):
        source = default_source

    str_builder = [sanitize(name),
                   "source=" + sanitize(source),
                   "traceId=" + str(trace_id),
                   "spanId=" + str(span_id)]
    if parents is not None:
        for uuid in parents:
            str_builder.append("parent=" + str(uuid))
    if follows_from is not None:
        for uuid in follows_from:
            str_builder.append("followsFrom=" + str(uuid))
    if tags is not None:
        for key, val in tags:
            if is_blank(key):
                raise ValueError("Span tag key cannot be blank")
            if is_blank(val):
                raise ValueError("Span tag val cannot be blank")
            str_builder.append(sanitize(key) + "=" + sanitize(val))
    str_builder.append(start_millis)
    str_builder.append(duration_millis)
    return ' '.join('{0}'.format(s) for s in str_builder) + "\n"
