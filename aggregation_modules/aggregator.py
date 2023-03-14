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
Functions to aggregate data
"""

import importlib
import json
import logging
import os
import sys
import time

from aggregation_modules import custom_functions
from aggregation_modules.provision_parser import ProvisionMetadata
from aggregation_modules.stream_parser import StreamMetadata
from aggregation_modules.utils import BaseUtils

logger = logging.getLogger(__name__)


def import_dynamic_modules(module_name):
    """
    dynamically import cloud services specific modules
    """
    # pylint: disable=broad-except
    try:
        return importlib.import_module(module_name)
    except ImportError as err:
        # warning
        logger.warning("%s: %s", type(err), err)
    except Exception as err:
        # failure on any other exception
        logger.fatal("%s: %s", type(err), err)
        sys.exit(err)
    return None


class Aggregator:
    """
    main class that reads metadata,
    input data and aggregates them
    """

    def __init__(self, cloud_provider=None):

        # setting time zone as UTC
        os.environ["TZ"] = "UTC"
        time.tzset()

        # variables
        self.all_fields_map = {}
        self.all_custom_functions = {}
        self.aggregate_column = "reqtimesec"

        # to hold class objects
        self.provision_metadata = None
        self.stream_metadata = None

        # input
        self.input_file = None

        # to hold the results
        self.dataframe = None
        self.result = {}
        self.result_map = []

        # supported other values: azure or aws
        self.cloud = cloud_provider

        # init cloud object
        self.cloud_storage_object = None
        self.init_cloud_storage_object()

    def init_cloud_storage_object(self):
        """
        sets cloud_storage_object for appropriate
        cloud service
        """

        if self.cloud is None:
            self.cloud_storage_object = BaseUtils()

        # import cloud modules and return object
        # for the respective cloud providers
        if self.cloud == "azure":
            self.azure = import_dynamic_modules("cloud_modules_azure.utils")
            self.cloud_storage_object = self.azure.AzureStorageContainer()

        if self.cloud == "aws":
            self.aws = import_dynamic_modules("cloud_modules_aws.utils")
            self.cloud_storage_object = self.aws.AWSStorageContainer()

    def read_metadata(self, read_provision=True):
        """
        Parent function to read all metadata/config files
        """
        self.read_all_datastream2_fields()
        self.read_all_custom_functions()
        self.read_stream_metadata()
        if read_provision:
            self.read_provision()

    def read_all_datastream2_fields(self):
        """
        reads the all_datastream2_fields.json file consisting of
        all field related details say, id, field name, functions etc
        """
        self.all_fields_map = self.cloud_storage_object.read_all_datastream2_fields_metadata()
        for i in self.all_fields_map:
            self.all_fields_map[i]["name"] = self.all_fields_map[i]["name"].lower(
            )

    def read_all_custom_functions(self):
        """
        reads all_custom_functions.json file and parse
        the functions details
        """
        self.all_custom_functions = (
            self.cloud_storage_object.read_all_custom_functions_metadata()
        )
        logger.debug("self.all_custom_functions: %s",
                     self.all_custom_functions)

    def read_stream_metadata(self):
        """
        reads <stream>.json file and parse
        stream related details
        """
        self.stream_metadata = StreamMetadata()
        stream_buffer = self.cloud_storage_object.read_stream_metadata()
        self.stream_metadata.populate_fields(
            stream_buffer, self.all_fields_map)

    def read_provision(self):
        """
        To read the provision file containing
        the list of functions to aggregate data
        """
        self.provision_metadata = ProvisionMetadata()
        prov_buffer = (
            self.cloud_storage_object.read_provision_metadata()
        )
        self.provision_metadata.populate_fields(
            prov_buffer, self.all_custom_functions)

    def read_input_data(self, input_file, bucket_name=None):
        """
        read the input file and sets the dataframe
        """

        self.input_file = input_file
        # from local dir
        if self.cloud is None:
            self.dataframe = self.cloud_storage_object.read_data_file_from_local(
                self.input_file,
                self.stream_metadata.stream_format,
                self.stream_metadata.get_stream_field_names(),
                self.provision_metadata.get_provision_field_names(),
            )

        # for azure
        if self.cloud == "azure":
            self.dataframe = self.cloud_storage_object.read_data_file_from_azure_blob(
                self.input_file,
                self.stream_metadata.stream_format,
                self.stream_metadata.get_stream_field_names(),
                self.provision_metadata.get_provision_field_names(),
            )

        # for aws
        if self.cloud == "aws":
            self.dataframe = self.cloud_storage_object.read_data_file_from_s3(
                bucket_name,
                self.input_file,
                self.stream_metadata.stream_format,
                self.stream_metadata.get_stream_field_names(),
                self.provision_metadata.get_provision_field_names(),
            )

    def get_custom_functions(self):
        """
        Gets all custom fields available to the user
        used for front end
        """
        available_custom_functions = {}

        stream_fields = self.stream_metadata.get_stream_field_names()
        logger.debug("all_stream_fields... \n%s",
                     json.dumps(stream_fields, indent=2))

        for custom_function, custom_function_spec in self.all_custom_functions.items():
            required_fields_exist = True
            for required_field in custom_function_spec["required-fields"]:
                if required_field not in stream_fields:
                    required_fields_exist = False

            if required_fields_exist:
                available_custom_functions[custom_function] = custom_function_spec[
                    "description"
                ]

        return available_custom_functions

    def process_data_per_ctxt(self, df_ctxt) -> dict:
        """
        reads dataframe and aggregate data
        """

        logger.debug(self.provision_metadata.fields_to_aggregate)
        # invoke selected aggregation functions for fields
        for col, function_list in self.provision_metadata.fields_to_aggregate.items():
            for function in function_list["funcs"]:
                if function in ["unique_counts"]:
                    self.result.update(
                        custom_functions.parse_unique_count_for_column(
                            df_ctxt[col], col)
                    )
                else:
                    key_name = str(col) + "_" + str(function)
                    self.result[key_name] = custom_functions.cal_base_aggregates(
                        function,
                        df_ctxt[col]
                    )

        # invoke selected custom aggregate functions
        for function in self.provision_metadata.custom_functions:
            if function == "get_status_code_level_hit_counts":
                self.result["total_hits"] = len(df_ctxt.index)

            if function == "get_status_code_level_hit_counts":
                self.result.update(
                    custom_functions.get_status_code_level_hit_counts(
                        df_ctxt["statuscode"])
                )

            if function == "get_cachestatus":
                self.result.update(
                    custom_functions.cal_cache_status(df_ctxt["cachestatus"])
                )

            if function == "get_traffic_volume":
                self.result["traffic_volume"] = custom_functions.get_traffic_volume(
                    df_ctxt["totalbytes"]
                )

            if function == "get_offload_rate":
                self.result["offload_rate"] = custom_functions.cal_offload_rate(
                    df_ctxt["cachestatus"]
                )

            if function == "get_origin_response_time":
                self.result[
                    "origin_response_time"
                ] = custom_functions.cal_origin_responsetime(
                    df_ctxt[
                        ["cachestatus", "cacherefreshsrc", "turnaroundtimemsec"]
                    ]
                )

            if function == "get_user_agent_details":
                self.result.update(
                    custom_functions.parse_user_agent(df_ctxt["ua"])
                )

            if function == "get_unique_visitor":
                self.result.update(custom_functions.calc_unique_visitor(df_ctxt[
                        ["ua", "cliip"]
                    ]))
        # all new custom defined functions can be invoked here
        return self.result

    def preprocess_dataframe(self):
        """
        pre process the dataframe constructed from the input data
        for integer columns sets non integer values to 0
        for non integer columns sets "-" to "others"
        """
        for column_name in self.provision_metadata.get_provision_field_names():
            # integer fields
            if self.stream_metadata.get_data_type_for_field(column_name) == "bigint":
                self.dataframe[column_name] = custom_functions.convert_to_numeric(
                    self.dataframe[column_name])

            # string fields
            if self.stream_metadata.get_data_type_for_field(column_name) == "string":
                self.dataframe[column_name] = custom_functions.replace_string(
                    self.dataframe[column_name], "-", "others")

    def process_data(self) -> dict:
        """
        reads dataframe and aggregate data
        """

        self.preprocess_dataframe()
        if self.provision_metadata.aggregation_interval > 0:
            self.dataframe["aggregated_time"] = self.dataframe.apply(
                lambda x: custom_functions.convert_time(
                    x[self.aggregate_column],
                    delta=self.provision_metadata.aggregation_interval), axis=1)
            logger.debug(
                "top 5 rows with aggregated time interval[aggregated_time]... \n%s",
                self.dataframe.head(5))
            logger.debug("unique time intervals in the dataset: %s",
                         self.dataframe["aggregated_time"].unique())

            # for each agg interval process the data
            for agg_timestamp in self.dataframe["aggregated_time"].unique():
                self.result = {"start_timestamp": int(agg_timestamp)}
                self.process_data_per_ctxt(
                    self.dataframe[self.dataframe["aggregated_time"] == agg_timestamp])
                self.result_map.append(self.result)
        else:
            self.result = {}
            self.process_data_per_ctxt(self.dataframe)
            self.result_map.append(self.result)

        return self.result_map
