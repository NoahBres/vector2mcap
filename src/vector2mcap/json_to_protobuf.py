"""Convert JSON objects to protobuf messages."""

from datetime import datetime
from typing import Dict, Any, Optional

from google.protobuf.timestamp_pb2 import Timestamp
from rich.console import Console

from . import event_pb2


console = Console()


def convert_timestamp(timestamp_str: str) -> Timestamp:
    """Convert ISO 8601 timestamp string to protobuf Timestamp.

    Args:
        timestamp_str: ISO 8601 formatted timestamp string

    Returns:
        Protobuf Timestamp object
    """
    # Parse ISO 8601 timestamp
    dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

    timestamp = Timestamp()
    timestamp.FromDatetime(dt)
    return timestamp


def convert_metric_kind(kind_str: str) -> event_pb2.Metric.Kind:
    """Convert string metric kind to protobuf enum.

    Args:
        kind_str: String representation of metric kind

    Returns:
        Protobuf Metric.Kind enum value
    """
    kind_map = {
        "incremental": event_pb2.Metric.Kind.Incremental,
        "absolute": event_pb2.Metric.Kind.Absolute,
    }
    return kind_map.get(kind_str.lower(), event_pb2.Metric.Kind.Absolute)


def convert_tags(tags_dict: Dict[str, str]) -> Dict[str, str]:
    """Convert tags dictionary to protobuf format.

    Args:
        tags_dict: Dictionary of tag key-value pairs

    Returns:
        Dictionary suitable for protobuf string map
    """
    return {str(k): str(v) for k, v in tags_dict.items()}


def json_to_metric(json_obj: Dict[str, Any]) -> Optional[event_pb2.Metric]:
    """Convert a JSON object containing metric data to a protobuf Metric.

    Args:
        json_obj: JSON object from JSONL file

    Returns:
        Protobuf Metric object, or None if conversion fails
    """
    try:
        # Check if this is a metric object
        if "metric" not in json_obj:
            console.print(
                f"[yellow]Warning: JSON object missing 'metric' field, skipping[/yellow]"
            )
            return None

        metric_data = json_obj["metric"]

        # Create protobuf Metric
        metric = event_pb2.Metric()

        # Required fields
        if "name" in metric_data:
            metric.name = metric_data["name"]
        else:
            console.print(
                "[yellow]Warning: Metric missing 'name' field, skipping[/yellow]"
            )
            return None

        if "timestamp" in metric_data:
            metric.timestamp.CopyFrom(convert_timestamp(metric_data["timestamp"]))
        else:
            console.print(
                "[yellow]Warning: Metric missing 'timestamp' field, skipping[/yellow]"
            )
            return None

        # Optional fields
        if "namespace" in metric_data:
            metric.namespace = metric_data["namespace"]

        if "tags" in metric_data:
            tags = convert_tags(metric_data["tags"])
            metric.tags_v1.update(tags)

        if "kind" in metric_data:
            metric.kind = convert_metric_kind(metric_data["kind"])

        # Handle metric value types
        if "counter" in metric_data:
            counter = event_pb2.Counter()
            counter.value = float(metric_data["counter"]["value"])
            metric.counter.CopyFrom(counter)
        elif "gauge" in metric_data:
            gauge = event_pb2.Gauge()
            gauge.value = float(metric_data["gauge"]["value"])
            metric.gauge.CopyFrom(gauge)
        elif "set" in metric_data:
            set_metric = event_pb2.Set()
            if "values" in metric_data["set"]:
                set_metric.values.extend([str(v) for v in metric_data["set"]["values"]])
            metric.set.CopyFrom(set_metric)
        else:
            console.print(
                f"[yellow]Warning: Unknown metric type in: {metric_data.keys()}[/yellow]"
            )
            return None

        return metric

    except Exception as e:
        console.print(f"[red]Error converting JSON to metric: {e}[/red]")
        return None


def json_to_event_wrapper(json_obj: Dict[str, Any]) -> Optional[event_pb2.EventWrapper]:
    """Convert a JSON object to a protobuf EventWrapper.

    Args:
        json_obj: JSON object from JSONL file

    Returns:
        Protobuf EventWrapper object, or None if conversion fails
    """
    try:
        wrapper = event_pb2.EventWrapper()

        # Try to convert as metric first
        metric = json_to_metric(json_obj)
        if metric:
            wrapper.metric.CopyFrom(metric)
            return wrapper

        # Could add support for logs and traces here in the future
        console.print(
            "[yellow]Warning: Unable to convert JSON object to any known event type[/yellow]"
        )
        return None

    except Exception as e:
        console.print(f"[red]Error creating EventWrapper: {e}[/red]")
        return None
