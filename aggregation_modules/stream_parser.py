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
used to parse stream file (stream.json) and populate
necessary fields that will be used for aggregation.
"""

import logging

logger = logging.getLogger(__name__)


class Fields:
    def __init__(self, dataset_id, dataset_name, dataset_type):
        self.id = dataset_id
        self.name = dataset_name
        self.dtype = dataset_type


class StreamMetadata:
    def __init__(self):

        self.stream_activation_status = None
        self.delimiter = None
        self.stream_format = None
        self.__chosen_fields = []  # list of objects of class Fields

    def __str__(self):
        """
        outputs all the members of the class
        """
        return "Stream Metadata-> \n\t Activation-Status : {},\n\t Delimiter : {},\n\t Format : {},\n\t Field Names : {}\n".format(
            self.stream_activation_status,
            self.delimiter,
            self.stream_format,
            self.chosenFieldsNames,
        )

    def get_datasetids(self, stream_datasets) -> list:
        """
        Returns the ordered list of dataset ids
        """

        rslt = {}
        for dataset in stream_datasets:
            for datafield in dataset["datasetFields"]:
                rslt[datafield.get("order", datafield["datasetFieldId"])] = str(
                    datafield["datasetFieldId"]
                )

        # return array as specified in the order
        return [val for _, val in sorted(rslt.items())]

    def populate_fields(self, stream_buffer, all_ds_fields):
        """
        sets self.__chosen_fields containing the dataset ids
        and name for the particular stream
        """
        try:
            self.stream_activation_status = stream_buffer.get(
                "activationStatus")
            if "config" in stream_buffer:
                self.stream_format = stream_buffer["config"].get("format")
                self.delimiter = stream_buffer["config"].get("delimiter")
        except Exception as err:
            logger.error(
                "%s: Stream activationStatus or config format/delimiter not set: %s",
                type(err),
                err,
            )

        chosen_ids = self.get_datasetids(stream_buffer.get("datasets", []))

        self.__chosen_fields.append(Fields(None, "version", "bigint"))
        for field_id in chosen_ids:
            try:
                self.__chosen_fields.append(
                    Fields(
                        field_id,
                        all_ds_fields[field_id]["name"].lower(),
                        all_ds_fields[field_id]["dtype"]
                    )
                )

            except Exception as err:
                logger.warn(
                    "%s: key %s not found in all_fields_map ", err, field_id)

        logger.debug("stream fields... \n%s", self.get_stream_field_names())

    def get_stream_field_names(self):
        """
        returns the list of field names
        """
        return [field.name for field in self.__chosen_fields]

    def get_stream_ids(self):
        """
        returns the list of field ids
        """
        return [field.id for field in self.__chosen_fields]

    def get_data_type_for_field(self, field_name):
        """
        returns the datatype of the field_name
        """
        for field in self.__chosen_fields:
            if field.name == field_name:
                return field.dtype
