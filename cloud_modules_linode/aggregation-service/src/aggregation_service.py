import json
import logging
import os

import boto3

from aggregation_modules.aggregator import Aggregator
from config import Config

logger = logging.getLogger(__name__)


class AggregationService:
    def __init__(self):
        pass

    @staticmethod
    def _get_s3_client(service: str):
        config_map = {
            "input": (
                Config.DATA_INPUT_STORAGE_REGION,
                Config.DATA_INPUT_STORAGE_ACCESS_KEY,
                Config.DATA_INPUT_STORAGE_SECRET_KEY,
            ),
            "output": (
                Config.DATA_OUTPUT_STORAGE_REGION,
                Config.DATA_OUTPUT_STORAGE_ACCESS_KEY,
                Config.DATA_OUTPUT_STORAGE_SECRET_KEY,
            ),
            "config": (
                Config.CONFIG_STORAGE_REGION,
                Config.CONFIG_STORAGE_ACCESS_KEY,
                Config.CONFIG_STORAGE_SECRET_KEY,
            ),
        }
        if service not in config_map:
            raise ValueError("Unknown service type")
        region, access_key, secret_key = config_map[service]
        endpoint_url = f"https://{region}-1.linodeobjects.com"
        return boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )

    def _download_file(self, filename: str) -> str:
        logger.info(f"Downloading file {filename}")
        s3 = self._get_s3_client("input")
        bucket = Config.DATA_INPUT_STORAGE_NAME
        dst = os.path.join("/tmp", filename)
        s3.download_file(bucket, filename, dst)
        logger.info(f"Downloaded file {filename} to {dst}")
        return dst

    def _upload_file(self, local_path: str, filename: str):
        logger.info(f"Uploading file {filename}")
        boto3.set_stream_logger('botocore', level=logging.DEBUG)

        s3 = self._get_s3_client("output")
        bucket = Config.DATA_OUTPUT_STORAGE_NAME
        logger.info(f"Uploading file {filename} (local_path: {local_path}) to {bucket}")
        logger.info(f"File size: {os.path.getsize(local_path)} bytes")
        s3.upload_file(local_path, bucket, filename)
        logger.info(f"Uploaded file {filename} to bucket {bucket}")

    def _remove_input_file(self, filename: str):
        logger.info(f"Removing input file {filename}")
        s3 = self._get_s3_client("input")
        bucket = Config.DATA_INPUT_STORAGE_NAME
        s3.delete_object(Bucket=bucket, Key=filename)
        logger.info(f"Removed input file {filename} from bucket {bucket}")

    @staticmethod
    def _execute_aggregation(input_path: str, output_path: str, cloud: str = None):
        obj = Aggregator(cloud_provider=None)
        obj.read_metadata()
        obj.read_input_data(input_file=input_path, bucket_name=None)
        obj.process_data()
        with open(output_path, "w") as f:
            json.dump(obj.result_map, f, indent=2)

    def process_file(self, filename: str):
        try:
            local_input = self._download_file(filename)
            local_output = f"/tmp/aggregated_{filename}"
            self._download_configs()
            self._execute_aggregation(local_input, local_output)
            self._upload_file(local_output, f"aggregated_{filename}")
            self._remove_input_file(filename)
            os.remove(local_input)
            os.remove(local_output)
        except Exception as e:
            logger.error(f"Error processing file: {filename}, Error: {e}")
            raise e

    def _download_configs(self):
        """
        Download config files from the config bucket and save them to /app/configs
        """
        logger.info(f"Downloading config files")
        config_dir = "/app/configs"
        os.makedirs(config_dir, exist_ok=True)

        s3 = self._get_s3_client("config")
        bucket = Config.CONFIG_STORAGE_NAME

        files = [
            "all_custom_functions.json",
            "all_datastream2_fields.json",
            "provision.json",
            "stream.json"
        ]
        for filename in files:
            dst = os.path.join(config_dir, filename)
            s3.download_file(bucket, filename, dst)
            logger.info(f"Downloaded file {filename} to {dst}")
