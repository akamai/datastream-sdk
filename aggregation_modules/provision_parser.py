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
Methods to parse provision file (provision.json) and populate
necessary fields that will be used for aggregation.
"""

import logging
import json

logger = logging.getLogger(__name__)


class ProvisionMetadata:
    """
    provision class
    """

    def __init__(self):
        self.__data = {}
        self.fields_to_aggregate = {}
        self.custom_functions = {}
        self.aggregation_interval = -1

    def __str__(self) -> str:
        return f"ProvisionMetadata obj, fields={self.fields_to_aggregate}, custom_fields={self.custom_functions}"

    def populate_fields(self, provbuffer, all_custom_functions):
        """
        sets the following args by reading the provbuffer
        self.fields_to_aggregate containing the dataset fields that are needed to calculate basic aggregations
        and self.custom_functions containing the enabled list of custom fuctions
        """

        logger.debug(f"all_custom_functions: {all_custom_functions}")
        # read provision file
        self.__data = {k.lower(): v for k, v in provbuffer.items()}

        # construct the necessary fields needed to apply
        # basic aggregate functions and custom functions
        for func_name in self.__data.keys():

            if func_name not in ["custom-functions", "aggregation-interval"]:
                self.fields_to_aggregate[func_name] = {
                    "funcs": self.__data[func_name],
                }

            if func_name == "aggregation-interval":
                self.aggregation_interval = self.__data[func_name]
                if self.aggregation_interval > 0:
                    # add reqtimesec to the required field set
                    self.fields_to_aggregate["reqtimesec"] = {"funcs": []}

            if func_name == "custom-functions":
                for function in self.__data["custom-functions"]:
                    if function not in all_custom_functions:
                        logger.debug(
                            "function invalid or not defined: %s", function)
                        continue

                    self.custom_functions[function] = {
                        "funcs": [],
                    }
                    # append the fields used for dependent functions
                    for dep_field in all_custom_functions[function].get(
                        "required-fields"
                    ):
                        # check to prevent overriding of any aggregates
                        if dep_field not in self.fields_to_aggregate:
                            self.fields_to_aggregate[dep_field] = {
                                "funcs": [],
                            }

        logger.debug(
            "provision_metadata.fields_to_aggregate... \n%s",
            json.dumps(self.fields_to_aggregate, indent=2),
        )
        logger.debug(
            "provision_metadata.custom_functions... \n%s",
            json.dumps(self.custom_functions, indent=2),
        )

    def get_provision_field_names(self):
        """
        returns the list of field names
        from the provision file
        """
        return list(self.fields_to_aggregate.keys())
