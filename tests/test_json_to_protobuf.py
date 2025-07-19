"""Tests for JSON to protobuf conversion."""

import pytest
from datetime import datetime

from vector2mcap.json_to_protobuf import (
    convert_timestamp,
    convert_metric_kind,
    convert_tags,
    json_to_metric,
    json_to_event_wrapper,
)
from vector2mcap import event_pb2


def test_convert_timestamp():
    """Test timestamp conversion."""
    timestamp_str = "2025-07-16T14:20:06.666956352Z"
    result = convert_timestamp(timestamp_str)

    assert result.seconds > 0
    assert result.nanos > 0


def test_convert_metric_kind():
    """Test metric kind conversion."""
    assert convert_metric_kind("absolute") == event_pb2.Metric.Kind.Absolute
    assert convert_metric_kind("incremental") == event_pb2.Metric.Kind.Incremental
    assert convert_metric_kind("unknown") == event_pb2.Metric.Kind.Absolute  # default


def test_convert_tags():
    """Test tags conversion."""
    tags = {"host": "test-host", "component": "test"}
    result = convert_tags(tags)

    assert result["host"] == "test-host"
    assert result["component"] == "test"


def test_json_to_metric_counter():
    """Test converting JSON counter metric to protobuf."""
    json_data = {
        "metric": {
            "name": "test_counter",
            "namespace": "test",
            "tags": {"host": "test-host"},
            "timestamp": "2025-07-16T14:20:06.666956352Z",
            "kind": "absolute",
            "counter": {"value": 42.0},
        }
    }

    result = json_to_metric(json_data)

    assert result is not None
    assert result.name == "test_counter"
    assert result.namespace == "test"
    assert result.tags_v1["host"] == "test-host"
    assert result.kind == event_pb2.Metric.Kind.Absolute
    assert result.counter.value == 42.0


def test_json_to_metric_gauge():
    """Test converting JSON gauge metric to protobuf."""
    json_data = {
        "metric": {
            "name": "test_gauge",
            "namespace": "test",
            "tags": {"host": "test-host"},
            "timestamp": "2025-07-16T14:20:06.666956352Z",
            "kind": "absolute",
            "gauge": {"value": 100.5},
        }
    }

    result = json_to_metric(json_data)

    assert result is not None
    assert result.name == "test_gauge"
    assert result.gauge.value == 100.5


def test_json_to_metric_missing_required_field():
    """Test handling missing required fields."""
    json_data = {
        "metric": {
            "namespace": "test",
            "tags": {"host": "test-host"},
            "timestamp": "2025-07-16T14:20:06.666956352Z",
            "kind": "absolute",
            "counter": {"value": 42.0},
        }
    }

    result = json_to_metric(json_data)
    assert result is None  # Should return None for missing name


def test_json_to_event_wrapper():
    """Test converting JSON to EventWrapper."""
    json_data = {
        "metric": {
            "name": "test_counter",
            "namespace": "test",
            "tags": {"host": "test-host"},
            "timestamp": "2025-07-16T14:20:06.666956352Z",
            "kind": "absolute",
            "counter": {"value": 42.0},
        }
    }

    result = json_to_event_wrapper(json_data)

    assert result is not None
    assert result.metric.name == "test_counter"
    assert result.metric.counter.value == 42.0


def test_json_to_event_wrapper_invalid():
    """Test handling invalid JSON data."""
    json_data = {"invalid": "data"}

    result = json_to_event_wrapper(json_data)
    assert result is None
