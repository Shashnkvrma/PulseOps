import os
import time
import urllib.request
import json
import redis
from dotenv import load_dotenv


load_dotenv()


SERVICE_URL = os.getenv("SERVICE_URL")


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_QUEUE = os.getenv("REDIS_QUEUE", "pulseops_events")


# Redis connection
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)


# Remembers whether we have already detected this outage
service_was_down = False


def check_service():
    global service_was_down

    try:
        response = urllib.request.urlopen(
            SERVICE_URL,
            timeout=3
        )

        if response.status == 200:
            print("Service is healthy")

            # Service recovered
            if service_was_down:
                print("Service recovered")

            service_was_down = False
            return True

    except Exception:
        print("Service is DOWN")

        # Send only one event when
        # HEALTHY → DOWN happens
        if not service_was_down:
            send_event_to_redis()
            service_was_down = True
        else:
            print("Event already sent for this outage")

        return False


def determine_severity():
    # For now, a completely unavailable service is HIGH severity.
    return "high"


def send_event_to_redis():

    event = {
        "service_name": "demo-service",
        "event": "SERVICE_DOWN",
        "severity": determine_severity()
    }

    try:
        redis_client.lpush(
            REDIS_QUEUE,
            json.dumps(event)
        )

        print("Event sent to Redis:", event)

    except Exception as error:
        print("Failed to send event to Redis:", error)


while True:
    check_service()
    time.sleep(5)