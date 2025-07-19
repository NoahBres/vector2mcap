# vector2mcap CLI Tool - Project Plan

## Overview
A Python CLI tool that converts Vector JSONL telemetry files to MCAP format using protobuf serialization.

## Architecture

### Core Components

1. **CLI Interface** (`cli.py`)
   - Uses Click for argument parsing
   - Supports glob patterns for input files
   - Output file specification with `-o` flag

2. **Protobuf Schema** (`event_pb2.py`)
   - Generated from Vector's event.proto
   - Defines Metric, Counter, Gauge, and related message types

3. **JSON to Protobuf Converter** (`converter.py`)
   - Parses JSONL input files
   - Maps JSON fields to protobuf message fields
   - Handles timestamp conversion and metric type detection

4. **MCAP Writer** (`mcap_writer.py`)
   - Integrates with mcap-protobuf-support library
   - Registers protobuf schema
   - Writes protobuf messages to MCAP format

5. **File Processing** (`file_processor.py`)
   - Handles glob pattern expansion
   - Processes multiple JSONL files sequentially
   - Error handling for malformed files

### Data Flow

```
JSONL Files → JSON Parser → Protobuf Converter → MCAP Writer → output.mcap
```

### Dependencies

- **mcap-protobuf-support**: MCAP format support with protobuf
- **protobuf**: Protocol buffer library
- **click**: CLI framework
- **rich**: Progress bars and console output (optional)

## Implementation Steps

- [ ] **Project Setup**: Initialize Python project with uv and dependencies
- [ ] **Generate Protobuf Bindings**: Create Python classes from event.proto
- [ ] **CLI Interface**: Implement command-line argument parsing
- [ ] **File Reader**: Support glob patterns and JSONL parsing
- [ ] **JSON to Protobuf Converter**: Map JSON fields to protobuf messages
- [ ] **MCAP Writer**: Integrate protobuf messages with MCAP format
- [ ] **Error Handling**: Validation and graceful error recovery
- [ ] **Testing**: Unit tests for all components
- [ ] **Logging**: Progress reporting and debug information
- [ ] **Documentation**: Usage examples and API documentation

## Key Challenges

1. **Schema Mapping**: Converting Vector's JSON metric format to protobuf
2. **Timestamp Handling**: Converting ISO 8601 strings to protobuf timestamps
3. **Metric Type Detection**: Mapping JSON metric types to protobuf oneof fields
4. **Large File Handling**: Memory-efficient processing of large JSONL files
5. **Error Recovery**: Handling malformed JSON lines gracefully

## Example Usage

```bash
# Single file
vector2mcap metrics.out -o output.mcap

# Multiple files with glob
vector2mcap "*.out" -o combined.mcap

# With verbose output
vector2mcap "logs/*.jsonl" -o result.mcap --verbose
```

## Schema Mapping Notes

Based on the sample JSONL data, the mapping will be:

- `metric.name` → `Metric.name`
- `metric.namespace` → `Metric.namespace`
- `metric.timestamp` → `Metric.timestamp` (converted to protobuf Timestamp)
- `metric.tags` → `Metric.tags_v1` (string map)
- `metric.kind` → `Metric.kind` (enum: "absolute" → Absolute)
- `metric.counter.value` → `Counter.value` (in Metric.value oneof)