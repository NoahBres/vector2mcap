# vector2mcap

Convert Vector JSONL telemetry files to MCAP format using protobuf serialization.

## Installation

```bash
uv add vector2mcap
```

Or for development:

```bash
git clone <repository>
cd vector2mcap
uv sync
```

## Usage

### Basic Usage

Convert a single JSONL file:

```bash
vector2mcap metrics.out -o output.mcap
```

### Glob Patterns

Convert multiple files using glob patterns:

```bash
vector2mcap "*.out" -o combined.mcap
vector2mcap "logs/*.jsonl" -o result.mcap
```

### Verbose Output

Enable verbose output to see progress and statistics:

```bash
vector2mcap "*.out" -o output.mcap --verbose
```

## Input Format

The tool expects JSONL (newline-delimited JSON) files where each line contains a Vector metric event. Example:

```json
{"metric":{"name":"component_received_events_total","namespace":"vector","tags":{"component_id":"stream","component_kind":"sink","component_type":"vector","host":"processor-v3-7"},"timestamp":"2025-07-16T14:20:06.666956352Z","kind":"absolute","counter":{"value":0.0}}}
```

### Supported Metric Types

- **Counter**: Monotonic numeric values
- **Gauge**: Point-in-time numeric values  
- **Set**: Collections of unique string values

## Output Format

The tool generates MCAP files containing protobuf-serialized Vector events. The protobuf schema is based on Vector's official `event.proto` definition.

## CLI Options

- `INPUT_PATTERNS...`: One or more file paths or glob patterns
- `-o, --output PATH`: Output MCAP file path (required)
- `-v, --verbose`: Enable verbose output with progress bars
- `--help`: Show help message

## Development

### Running Tests

```bash
uv run pytest
```

### Project Structure

```
src/vector2mcap/
  cli.py              # Command-line interface
  converter.py        # Main conversion orchestration
  file_reader.py      # JSONL file reading utilities
  json_to_protobuf.py # JSON to protobuf conversion
  mcap_writer.py      # MCAP file writing with protobuf
  event_pb2.py        # Generated protobuf bindings
  event.proto         # Vector protobuf schema
```

### Dependencies

- **click**: CLI framework
- **mcap-protobuf-support**: MCAP format with protobuf support
- **protobuf**: Protocol buffer library
- **rich**: Enhanced console output and progress bars

## Error Handling

The tool is designed to be robust:

- **Invalid JSON lines**: Skipped with warnings
- **Missing files**: Reported but processing continues
- **Unsupported metric types**: Logged as warnings
- **Missing required fields**: Messages skipped gracefully

## Schema Mapping

The tool maps Vector's JSON metric format to protobuf as follows:

| JSON Field | Protobuf Field | Notes |
|------------|----------------|-------|
| `metric.name` | `Metric.name` | Required |
| `metric.namespace` | `Metric.namespace` | Optional |
| `metric.timestamp` | `Metric.timestamp` | ISO 8601 � protobuf Timestamp |
| `metric.tags` | `Metric.tags_v1` | String map |
| `metric.kind` | `Metric.kind` | "absolute"/"incremental" � enum |
| `metric.counter.value` | `Counter.value` | In Metric.value oneof |
| `metric.gauge.value` | `Gauge.value` | In Metric.value oneof |
| `metric.set.values` | `Set.values` | In Metric.value oneof |