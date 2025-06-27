# Copyright 2020 Akamai Technologies, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Contains functions to interact with AWS storage
"""
import io
import logging
import os

import boto3
from aggregation_modules.utils import BaseUtils

logger = logging.getLogger(__name__)


class AWSStorageContainer(BaseUtils):
    """
    Functions to read config and date from S3 storage
    """

    def __init__(self):
        """
        init bucket name and boto3 client for s3
        """
        # init base class
        super().__init__()

        # s3 variables
        self.metadata_bucket = None
        self.metadata_path = None

        # s3 client from boto3
        self.s3_client = None

        # init metadata bucket and s3_client
        self.set_metadata_bucket()
        self.set_s3_client()

    def set_metadata_bucket(self):
        """
        returns bucket name configured
        """
        try:
            self.metadata_bucket = os.environ.get("S3_METADATA_BUCKET")
            self.metadata_path = os.environ.get("S3_METADATA_PATH")
        except Exception as err:
            logger.error(
                "Err: set variable S3_METADATA_BUCKET to your metadata bucketname "
            )
            logger.error("%s: %s", type(err), err)

    def set_s3_client(self):
        """
        returns boto3 client for s3
        """
        try:
            self.s3_client = boto3.client("s3")
        except Exception as err:
            logger.error("Error creating boto3 client for s3")
            logger.error("%s: %s", type(err), err)

    def read_from_s3(self, bucket, file_to_read) -> io.BytesIO:
        """
        returns an io buffer handle to read from
        """

        if self.s3_client is None:
            self.set_s3_client()

        response = None
        try:
            logger.debug("reading file: %s from bucket: %s",
                         file_to_read, bucket)
            response = self.s3_client.get_object(
                Bucket=bucket, Key=file_to_read)
            return self.get_bytes_io_buffer(response["Body"].read())
        except Exception as err:
            logger.error("%s: %s", type(err), err)
        return response

    def read_json_metadata_from_s3(self, json_file) -> dict:
        """
        reads json_file from s3 storage
        and return dict object
        """
        logger.info(f"read_json_metadata_from_s3: {json_file}")
        try:

            if self.metadata_path is not None:
                json_file_path = self.metadata_path + "/" + json_file

            logger.info("reading json file, metadata_path: %s", self.metadata_path)

            json_buffer = self.read_from_s3(
                self.metadata_bucket, json_file_path)
            return self.get_dict_from_json(json_buffer)
        except Exception as err:
            logger.error("%s: %s", type(err), err)
        return {}

    def read_all_datastream2_fields_metadata(self) -> dict:
        """
        reads all_datastream2_fields.json file,
        containing all the dataset fields avaiable in datastream,
        from blob and returns the dict
        """
        return self.read_json_metadata_from_s3(
            self.input_configs["all_datastream2_fields"]
        )

    def read_all_custom_functions_metadata(self) -> dict:
        """
        reads all_custom_functions.json file, 
        containing all the aggregate functions avaiable for datastream fields,
        from s3 storage and returns the dict
        """
        return self.read_json_metadata_from_s3(
            self.input_configs["all_custom_functions"]
        )

    def read_stream_metadata(self) -> dict:
        """
        reads stream.json file,
        containing stream specific details, 
        from s3 storage and returns the dict
        """
        return self.read_json_metadata_from_s3(self.input_configs["stream_file"])

    def read_provision_metadata(self) -> dict:
        """
        reads provision.json file, 
        containing the selected aggregate functions,
        from s3 storage and returns the dict
        """

        return self.read_json_metadata_from_s3(self.input_configs["provision_file"])

    def read_data_file_from_s3(
        self, bucket, filename, file_format, chosen_field_names, custom_columns
    ):
        """
        read input data file and returns a dataframe
        """

        data_buffer = self.read_from_s3(bucket, filename)
        return self.read_data_file(
            data_buffer, file_format, chosen_field_names, custom_columns
        )
