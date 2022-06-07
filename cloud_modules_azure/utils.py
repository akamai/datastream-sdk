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
Contains functions to interact with Azure Blob
"""

import io
import logging
import os

from aggregation_modules.utils import BaseUtils

from azure.storage.blob import BlobServiceClient

logger = logging.getLogger(__name__)


class AzureStorageContainer(BaseUtils):
    """
    Functions to read config and date from Azure Blob storage
    """

    def __init__(self):
        """
        init
        """
        # init base class
        super().__init__()

        # Create BlobServiceClient from a Connection String
        self.blob_service_client_for_metadata = None
        self.connect_info = {}

        # Init Container Clients to read metadata
        self.set_blob_service_client()

    def set_blob_service_client(self):
        """
        sets client to interact with a specific container
        """

        try:
            self.connect_info["azure_metadata_storage_connectionstring"] = os.getenv(
                'AzureMetadataStorageConnectionString')
            self.connect_info["metadata_container_name"] = os.getenv(
                'AzureMetadataStorageContainer')

            self.blob_service_client_for_metadata = (
                BlobServiceClient.from_connection_string(
                    self.connect_info["azure_metadata_storage_connectionstring"]
                )
            )
        except Exception as err:
            logger.error("%s: %s", type(err), err)
        return None

    def read_from_blob(self, file_name) -> io.BytesIO:
        """
        reads the file_name from blob
        and returns ByteIO
        """
        try:
            # Get a client to interact with the specified blob.
            blob_client = self.blob_service_client_for_metadata.get_blob_client(
                container=self.connect_info["metadata_container_name"],
                blob=file_name
            )
            # Downloads a blob to the StorageStreamDownloader
            download_stream = blob_client.download_blob()
            # to read all the content to bytesIO
            return self.get_bytes_io_buffer(download_stream.readall())

        except Exception as err:
            logger.error("%s: %s", type(err), err)
        return None

    def read_json_metadata_from_blob(self, json_file) -> dict:
        """
        read json file from blob storage
        and return dict object
        """
        try:
            json_buffer = self.read_from_blob(json_file)
            # return json.loads(json_content)
            return self.get_dict_from_json(json_buffer)

        except Exception as err:
            logger.error("%s: %s", type(err), err)
        return {}

    def read_all_datastream2_fields_metadata(self) -> dict:
        """
        reads all_datastream2_fields.json file,
        containing all the dataset fields avaiable in datastream,
        from blob storage and returns the dict
        """
        return self.read_json_metadata_from_blob(
            self.input_configs["all_datastream2_fields"]
        )

    def read_all_custom_functions_metadata(self) -> dict:
        """
        reads all_custom_functions.json file,
        containing all the aggregate functions avaiable for datastream fields,
        from blob storage and returns the dict
        """
        return self.read_json_metadata_from_blob(
            self.input_configs["all_custom_functions"]
        )

    def read_stream_metadata(self) -> dict:
        """
        reads stream.json file,
        containing stream specific details,
        from blob storage and returns the dict
        """
        # TODO: add info
        return self.read_json_metadata_from_blob(self.input_configs["stream_file"])

    def read_provision_metadata(self) -> dict:
        """
        reads provision.json file,
        containing the selected aggregate functions,
        from blob storage and returns the dict
        """
        return self.read_json_metadata_from_blob(self.input_configs["provision_file"])

    def read_data_file_from_azure_blob(
        self, filename, file_format, chosen_field_names, custom_columns
    ):
        """
        reads data file from azure blob store
        and returns pandas dataframe
        """

        data_buffer = self.get_bytes_io_buffer(filename.read())

        return self.read_data_file(
            data_buffer, file_format, chosen_field_names, custom_columns
        )
