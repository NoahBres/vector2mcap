"""Tests for MCAP data validation using mcap Python API."""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner
from mcap.reader import make_reader
from mcap_protobuf.decoder import DecoderFactory

from vector2mcap.cli import main
from vector2mcap import event_pb2


@pytest.fixture
def sample_mcap():
    """Create a temporary MCAP file with sample data."""
    jsonl_content = """{"metric":{"name":"test_counter","namespace":"vector","tags":{"host":"test-host","component_id":"test"},"timestamp":"2025-07-16T14:20:06.666956352Z","kind":"absolute","counter":{"value":42.0}}}
{"metric":{"name":"test_gauge","namespace":"vector","tags":{"host":"test-host","component_id":"test"},"timestamp":"2025-07-16T14:20:07.666956352Z","kind":"absolute","gauge":{"value":100.5}}}
{"metric":{"name":"test_set","namespace":"vector","tags":{"host":"test-host","component_id":"test"},"timestamp":"2025-07-16T14:20:08.666956352Z","kind":"absolute","set":{"values":["value1","value2"]}}}
"""
    
    # Create temporary JSONL file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as jsonl_file:
        jsonl_file.write(jsonl_content)
        jsonl_path = jsonl_file.name
    
    # Convert to MCAP
    with tempfile.NamedTemporaryFile(suffix=".mcap", delete=False) as mcap_file:
        runner = CliRunner()
        result = runner.invoke(main, [jsonl_path, "-o", mcap_file.name])
        assert result.exit_code == 0
        
        # Clean up JSONL file
        Path(jsonl_path).unlink()
        
        return mcap_file.name


def test_mcap_file_metadata(sample_mcap):
    """Test MCAP file contains correct metadata."""
    with open(sample_mcap, "rb") as f:
        reader = make_reader(f)
        summary = reader.get_summary()
        
        # Check basic file statistics
        assert summary.statistics.message_count == 3
        assert summary.statistics.channel_count == 1
        assert summary.statistics.schema_count == 1
        
        # Check channel information
        assert len(summary.channels) == 1
        channel = list(summary.channels.values())[0]
        assert channel.topic == "vector_event"
        
        # Check schema information
        assert len(summary.schemas) == 1
        schema = list(summary.schemas.values())[0]
        assert schema.name == "event.EventWrapper"
        assert schema.encoding == "protobuf"
    
    # Clean up
    Path(sample_mcap).unlink()


def test_mcap_file_structure_validation(sample_mcap):
    """Test MCAP file structure is valid."""
    with open(sample_mcap, "rb") as f:
        reader = make_reader(f, validate_crcs=True)
        summary = reader.get_summary()
        
        # If we can read the summary without errors, the file structure is valid
        assert summary is not None
        assert summary.statistics.message_count > 0
        
        # Validate we can iterate through all messages without errors
        message_count = 0
        for schema, channel, message in reader.iter_messages():
            message_count += 1
            # Basic message validation
            assert message.log_time > 0
            assert message.publish_time > 0
            assert len(message.data) > 0
        
        assert message_count == summary.statistics.message_count
    
    # Clean up
    Path(sample_mcap).unlink()


def test_mcap_protobuf_decoding(sample_mcap):
    """Test MCAP messages can be decoded as protobuf."""
    decoder_factory = DecoderFactory()
    
    with open(sample_mcap, "rb") as f:
        reader = make_reader(f, decoder_factories=[decoder_factory])
        
        messages = list(reader.iter_messages())
        assert len(messages) == 3
        
        # Verify all messages are on the correct topic
        for schema, channel, message in messages:
            assert channel.topic == "vector_event"
        
        # Verify message structure and decode protobuf data
        for i, (schema, channel, message) in enumerate(messages):
            # Check basic message properties
            assert message.log_time > 0
            assert message.publish_time > 0
            assert message.sequence >= 0
            
            # Decode protobuf message
            event_wrapper = event_pb2.EventWrapper()
            event_wrapper.ParseFromString(message.data)
            
            # Verify protobuf structure
            assert event_wrapper.HasField("metric")
            metric = event_wrapper.metric
            assert metric.name != ""
            assert metric.namespace == "vector"
            assert len(metric.tags_v1) > 0
            assert metric.HasField("timestamp")
            
            # Verify metric type is one of the expected types
            metric_types = ["counter", "gauge", "set"]
            has_metric_type = any(metric.HasField(mt) for mt in metric_types)
            assert has_metric_type, f"Message {i} should have one of: {metric_types}"
    
    # Clean up
    Path(sample_mcap).unlink()


def test_mcap_topic_filtering(sample_mcap):
    """Test filtering messages by topic."""
    with open(sample_mcap, "rb") as f:
        reader = make_reader(f)
        
        # Filter messages by the vector_event topic
        vector_event_messages = list(
            reader.iter_messages(topics=["vector_event"])
        )
        
        # Should get all messages since they're all on vector_event topic
        assert len(vector_event_messages) == 3
        
        # Verify all messages are from the correct topic
        for schema, channel, message in vector_event_messages:
            assert channel.topic == "vector_event"
        
        # Test filtering by non-existent topic
        non_existent_messages = list(
            reader.iter_messages(topics=["non_existent_topic"])
        )
        assert len(non_existent_messages) == 0
    
    # Clean up
    Path(sample_mcap).unlink()


def test_mcap_chunk_information(sample_mcap):
    """Test MCAP chunk information."""
    with open(sample_mcap, "rb") as f:
        reader = make_reader(f)
        summary = reader.get_summary()
        
        # Check chunk statistics
        assert summary.statistics.chunk_count >= 1
        
        # Verify chunk indexes exist
        assert len(summary.chunk_indexes) >= 1
        
        # Check chunk properties
        for chunk_index in summary.chunk_indexes:
            assert chunk_index.message_start_time > 0
            assert chunk_index.message_end_time >= chunk_index.message_start_time
            assert chunk_index.chunk_start_offset >= 0
            assert chunk_index.chunk_length > 0
    
    # Clean up
    Path(sample_mcap).unlink()


def test_mcap_data_integrity(sample_mcap):
    """Test data integrity and chronological ordering."""
    decoder_factory = DecoderFactory()
    
    with open(sample_mcap, "rb") as f:
        reader = make_reader(f, decoder_factories=[decoder_factory])
        
        messages = list(reader.iter_messages())
        assert len(messages) == 3
        
        # Verify timestamps are in chronological order
        timestamps = [message.log_time for schema, channel, message in messages]
        assert timestamps == sorted(timestamps), "Messages should be in chronological order"
        
        # Verify each message has proper data integrity
        for i, (schema, channel, message) in enumerate(messages):
            # Check basic message properties
            assert message.log_time > 0, f"Message {i} should have valid log_time"
            assert message.publish_time > 0, f"Message {i} should have valid publish_time"
            assert message.log_time == message.publish_time, f"Message {i} log_time should equal publish_time"
            
            # Decode and validate protobuf data
            event_wrapper = event_pb2.EventWrapper()
            event_wrapper.ParseFromString(message.data)
            
            # Verify metric data integrity
            metric = event_wrapper.metric
            assert metric.name != "", f"Message {i} should have non-empty metric name"
            assert metric.namespace != "", f"Message {i} should have non-empty namespace"
            assert metric.HasField("timestamp"), f"Message {i} should have timestamp"
            
            # Verify timestamp consistency between MCAP and protobuf
            proto_timestamp_ns = metric.timestamp.ToNanoseconds()
            assert message.log_time == proto_timestamp_ns, f"Message {i} timestamps should match"
    
    # Clean up
    Path(sample_mcap).unlink()


def test_multiple_file_conversion_validation():
    """Test validation of MCAP created from multiple input files."""
    # Create multiple JSONL files
    jsonl1_content = """{"metric":{"name":"file1_counter","namespace":"vector","tags":{"host":"test-host","file":"1"},"timestamp":"2025-07-16T14:20:06.666956352Z","kind":"absolute","counter":{"value":10.0}}}"""
    jsonl2_content = """{"metric":{"name":"file2_gauge","namespace":"vector","tags":{"host":"test-host","file":"2"},"timestamp":"2025-07-16T14:20:07.666956352Z","kind":"absolute","gauge":{"value":20.0}}}"""
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f1, \
         tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f2, \
         tempfile.NamedTemporaryFile(suffix=".mcap", delete=False) as mcap_file:
        
        f1.write(jsonl1_content)
        f2.write(jsonl2_content)
        f1.flush()
        f2.flush()
        
        # Convert multiple files to MCAP
        runner = CliRunner()
        result = runner.invoke(main, [f1.name, f2.name, "-o", mcap_file.name])
        assert result.exit_code == 0
        
        # Validate with mcap Python API
        decoder_factory = DecoderFactory()
        with open(mcap_file.name, "rb") as f:
            reader = make_reader(f, decoder_factories=[decoder_factory])
            summary = reader.get_summary()
            
            # Should have 2 messages from 2 files
            assert summary.statistics.message_count == 2
            
            # Validate message content
            messages = list(reader.iter_messages())
            assert len(messages) == 2
            
            # Verify both messages can be decoded and have correct data
            for i, (schema, channel, message) in enumerate(messages):
                event_wrapper = event_pb2.EventWrapper()
                event_wrapper.ParseFromString(message.data)
                
                metric = event_wrapper.metric
                assert metric.namespace == "vector"
                assert "file" in metric.tags_v1, f"Message {i} should have 'file' tag"
                
                # Check that we have one counter and one gauge
                if metric.HasField("counter"):
                    assert metric.name == "file1_counter"
                    assert metric.tags_v1["file"] == "1"
                elif metric.HasField("gauge"):
                    assert metric.name == "file2_gauge" 
                    assert metric.tags_v1["file"] == "2"
                else:
                    assert False, f"Message {i} should have counter or gauge field"
        
        # Clean up
        Path(f1.name).unlink()
        Path(f2.name).unlink()
        Path(mcap_file.name).unlink()