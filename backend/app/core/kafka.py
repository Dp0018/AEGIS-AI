import json
import logging
import asyncio
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from app.core.config import settings

logger = logging.getLogger("aegisai.kafka")

# Global variables
producer: AIOKafkaProducer = None
consumer_task: asyncio.Task = None

async def init_kafka_producer() -> None:
    """Initialize the global AIOKafkaProducer."""
    global producer
    if producer is not None:
        return
    
    logger.info(f"Initializing Kafka producer connecting to: {settings.KAFKA_BOOTSTRAP_SERVERS}")
    try:
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        await producer.start()
        logger.info("Kafka producer started successfully.")
    except Exception as e:
        logger.error(f"Failed to start Kafka producer: {e}")
        producer = None

async def close_kafka_producer() -> None:
    """Close the global AIOKafkaProducer."""
    global producer
    if producer is not None:
        logger.info("Closing Kafka producer...")
        try:
            await producer.stop()
            logger.info("Kafka producer stopped.")
        except Exception as e:
            logger.error(f"Error closing Kafka producer: {e}")
        finally:
            producer = None

async def publish_kafka_event(topic: str, key: str, value: dict) -> None:
    """Publish an event to a Kafka topic."""
    global producer
    if producer is None:
        logger.warning(f"Kafka producer not initialized. Skipping publish to topic: {topic}")
        return
        
    try:
        # Key must be bytes
        key_bytes = key.encode("utf-8") if key else None
        await producer.send_and_wait(topic, value, key=key_bytes)
        logger.debug(f"Event published to {topic} [key={key}]")
    except Exception as e:
        logger.error(f"Failed to publish event to {topic}: {e}")

async def start_kafka_consumers() -> None:
    """Start background Kafka consumers to process telemetry-events and ticket-events."""
    global consumer_task
    consumer_task = asyncio.create_task(consume_telemetry_events())

async def stop_kafka_consumers() -> None:
    """Stop background Kafka consumers."""
    global consumer_task
    if consumer_task is not None:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        consumer_task = None

async def consume_telemetry_events() -> None:
    """Background loop consuming events from Kafka and broadcasting them to WebSockets."""
    from app.core.websocket import manager  # Avoid circular import
    
    logger.info(f"Starting Kafka consumer for telemetry-events...")
    consumer = AIOKafkaConsumer(
        "telemetry-events",
        "ticket-events",
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        group_id="aegisai-ws-broadcaster"
    )
    
    # Retry loop to wait for Kafka to be ready
    retry_count = 5
    for attempt in range(retry_count):
        try:
            await consumer.start()
            break
        except Exception as e:
            logger.warning(f"Failed to connect consumer (attempt {attempt+1}/{retry_count}): {e}")
            if attempt == retry_count - 1:
                logger.error("Consumer connection exhausted. Real-time websocket broadcast from Kafka is disabled.")
                return
            await asyncio.sleep(2)
            
    try:
        async for msg in consumer:
            logger.info(f"Received message from topic {msg.topic}: {msg.value}")
            # Key typically holds the thread_id
            thread_id = msg.key.decode("utf-8") if msg.key else None
            if thread_id:
                # Broadcast the telemetry action to connected WebSocket clients for this thread
                await manager.broadcast(thread_id, {
                    "topic": msg.topic,
                    "data": msg.value
                })
    except asyncio.CancelledError:
        logger.info("Kafka consumer loop cancelled.")
    except Exception as e:
        logger.error(f"Error in Kafka consumer loop: {e}")
    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped.")
