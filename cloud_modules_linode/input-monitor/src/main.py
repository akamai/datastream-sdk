import logging
import os
import sys

import requests

from config import Config
from storage_checker import StorageChecker

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

logger = logging.getLogger(__name__)


def notify_aggregation_service(new_files):
    if not new_files:
        logger.info("No new files to notify.")
        return
    url = os.getenv("AGGREGATION_SERVICE_URL", "http://aggregation-service:8000/notify-files")
    try:
        logger.info(f"Notifying aggregation service at {url} with files: {new_files}")
        resp = requests.post(url, json={"files": list(new_files)})
        resp.raise_for_status()
        logger.info(f"Aggregation service response: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.error(f"Failed to notify aggregation service: {e}")


def main():
    checker = StorageChecker(
        Config.DATA_INPUT_STORAGE_ACCESS_KEY,
        Config.DATA_INPUT_STORAGE_SECRET_KEY,
        Config.DATA_INPUT_STORAGE_REGION,
        Config.DATA_INPUT_STORAGE_NAME,
        Config.MONITOR_STORAGE_ACCESS_KEY,
        Config.MONITOR_STORAGE_SECRET_KEY,
        Config.MONITOR_STORAGE_REGION,
        Config.MONITOR_STORAGE_NAME,
    )

    new_files = checker.check_new_objects()
    notify_aggregation_service(new_files)


if __name__ == "__main__":
    logger.info("Starting input monitor...")
    main()
    logger.info("Finished input monitor.")
