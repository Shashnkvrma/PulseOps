import os
import redis
import json
import urllib.request
import logging
from dotenv import load_dotenv


load_dotenv()


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_QUEUE = os.getenv("REDIS_QUEUE", "pulseops_events")

PULSEOPS_URL = os.getenv("PULSEOPS_URL")


# --------------------------------------------------
# Logging
# --------------------------------------------------

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/pulseops.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("pulseops.worker")


# --------------------------------------------------
# Redis connection
# --------------------------------------------------

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)


# --------------------------------------------------
# Check for existing open incident
# --------------------------------------------------

def has_open_incident(service_name):
    try:
        response = urllib.request.urlopen(
            PULSEOPS_URL,
            timeout=3
        )

        incidents = json.loads(
            response.read().decode()
        )

        for incident in incidents:
            if (
                incident["service_name"] == service_name
                and incident["status"] == "open"
            ):
                return True

        return False

    except Exception as error:
        logger.error(
            "Failed to check existing incidents: %s",
            error
        )
        return False


# --------------------------------------------------
# Create incident
# --------------------------------------------------

def create_incident(event):

    service_name = event["service_name"]

    # Prevent duplicate open incidents
    if has_open_incident(service_name):
        logger.info(
            "Open incident already exists for %s. Skipping duplicate.",
            service_name
        )
        return

    payload = {
        "service_name": service_name,
        "title": "Demo service is down",
        "severity": event["severity"]
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        PULSEOPS_URL,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        response = urllib.request.urlopen(
            request,
            timeout=3
        )

        result = json.loads(
            response.read().decode()
        )

        logger.info(
            "Incident created by worker: %s",
            result
        )

    except Exception as error:
        logger.error(
            "Failed to create incident: %s",
            error
        )


# --------------------------------------------------
# Worker
# --------------------------------------------------

logger.info("PulseOps background worker started")

while True:

    try:
        event_data = redis_client.brpop(
            REDIS_QUEUE,
            timeout=5
        )

        if event_data:

            _, event_json = event_data

            logger.info(
                "Event received from Redis: %s",
                event_json
            )

            try:
                event = json.loads(event_json)

                if event["event"] == "SERVICE_DOWN":
                    logger.info(
                        "Processing SERVICE_DOWN event"
                    )

                    create_incident(event)

            except Exception as error:
                logger.error(
                    "Failed to process event: %s",
                    error
                )

    except redis.exceptions.TimeoutError:
        # No event arrived within 5 seconds.
        # Keep the worker alive and continue waiting.
        continue

    except Exception as error:
        logger.error(
            "Redis worker error: %s",
            error
        )