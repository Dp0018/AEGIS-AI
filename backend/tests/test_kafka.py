import asyncio
import pytest
import app.core.kafka

def run_async(coro):
    return asyncio.run(coro)

def test_kafka_producer_lifecycle():
    """Verify that the Kafka producer starts, publishes events, and stops correctly."""
    async def _test():
        # 1. Startup producer
        await app.core.kafka.init_kafka_producer()
        assert app.core.kafka.producer is not None, "Kafka producer should be initialized."

        # 2. Publish a test event
        test_payload = {"status": "ok", "message": "Verification test message for Kafka."}
        await app.core.kafka.publish_kafka_event("telemetry-events", "test-key-id", test_payload)

        # 3. Shutdown producer
        await app.core.kafka.close_kafka_producer()
        assert app.core.kafka.producer is None, "Kafka producer should be shut down."

    run_async(_test())
