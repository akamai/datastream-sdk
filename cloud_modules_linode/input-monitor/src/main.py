import logging
import sys

from config import Config
from storage_checker import StorageChecker

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

logger = logging.getLogger(__name__)


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

    checker.check_new_objects()


if __name__ == "__main__":
    logger.info("Starting input monitor...")
    logger.info("Config: %s", Config.__dict__)
    main()
    logger.info("Finished input monitor.")
