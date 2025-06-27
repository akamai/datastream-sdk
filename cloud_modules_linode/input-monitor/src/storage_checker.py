import json
import logging

import boto3
from botocore.client import BaseClient
from botocore.config import Config

logger = logging.getLogger(__name__)


class StorageChecker:
    def __init__(self, access_key: str, secret_key: str, region: str, bucket_name: str,
                 state_access_key: str, state_secret_key: str, state_region: str, state_bucket_name: str):

        linode_endpoint = f"https://{region}-1.linodeobjects.com"
        state_linode_endpoint = f"https://{state_region}-1.linodeobjects.com"

        self.s3_client: BaseClient = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=linode_endpoint,
        )

        self.state_s3_client: BaseClient = boto3.client(
            "s3",
            aws_access_key_id=state_access_key,
            aws_secret_access_key=state_secret_key,
            endpoint_url=state_linode_endpoint,
        )
        self.bucket_name: str = bucket_name
        self.state_bucket_name: str = state_bucket_name
        self.state_file: str = "state.json"

    def _load_state(self):
        try:
            response = self.state_s3_client.get_object(Bucket=self.state_bucket_name, Key=self.state_file)
            state = json.loads(response["Body"].read().decode("utf-8"))
            # Ensure state is a list
            if isinstance(state, dict):
                state = list(state.keys())
            return state
        except self.state_s3_client.exceptions.NoSuchKey:
            logger.info("State file not found, initializing empty state.")
            return []
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return []

    def _save_state(self, state):
        try:
            self.state_s3_client.put_object(
                Bucket=self.state_bucket_name,
                Key=self.state_file,
                Body=json.dumps(state)
            )
            logger.info("State saved successfully.")
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    def check_new_objects(self):
        try:
            state = set(self._load_state())
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            objects = response.get("Contents", [])
            current_keys = set(obj["Key"] for obj in objects)

            # Add new objects to state
            new_keys = current_keys - state
            for key in new_keys:
                logger.info(f"New object detected: {key}")

            # Remove objects from state if they no longer exist in the bucket
            removed_keys = state - current_keys
            for key in removed_keys:
                logger.info(f"Object removed from bucket, deleting from state: {key}")

            # Save the updated state as a list
            self._save_state(list(current_keys))
            return new_keys
        except Exception as e:
            logger.error(f"Error checking objects: {e}")
            return set()
