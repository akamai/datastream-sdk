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
Module to generate provision.json file
"""


import json
import sys

sys.path.append("..")

from aggregation_modules.aggregator import Aggregator
from django.contrib import messages
from django.shortcuts import render
from django.template.context_processors import csrf

class PassingFieldData:
    """
    Dataset Fields
    """

    def __init__(self, field_name, field_id, agg) -> None:
        self.field_name = field_name
        self.field_id = field_id
        self.field_agg_functions = agg


def home(request):
    """
    main function
    """

    passing_dict = {}
    aggregator_obj = Aggregator()

    # read metadata
    aggregator_obj.read_metadata(read_provision=False)

    # get aggregatable fields from all fields
    aggregate_fields_ids_with_agg = {i
                                     for i in aggregator_obj.all_fields_map
                                     if "agg" in aggregator_obj.all_fields_map[i]}

    # get fields in the stream
    stream_fields_ids = aggregator_obj.stream_metadata.get_stream_ids()

    # get aggregatable fields from fields in the stream
    all_field_ids = set(aggregate_fields_ids_with_agg) & set(stream_fields_ids)

    # build passing_dict by parsing configs
    passing_dict = {
        "data": [],
        "custom_functions": [],
        "allow_time_based_aggregation": False
    }

    # allow time based aggregation only if Request Time field is part of the stream
    if "1100" in stream_fields_ids:
        passing_dict["allow_time_based_aggregation"] = True

    # set "data"
    for field_id in sorted(all_field_ids):
        passing_dict["data"].append(
            PassingFieldData(
                aggregator_obj.all_fields_map[field_id]["name"],
                field_id,
                aggregator_obj.all_fields_map[field_id]["agg"],
            )
        )

    # set supported "custom_functions"
    passing_dict["custom_functions"] = aggregator_obj.get_custom_functions()

    # request
    if request.method == "POST":
        passing_dict.update(csrf(request))
        selected_fields = {i: request.POST[i] for i in request.POST}
        del selected_fields["csrfmiddlewaretoken"]

        # build fields_json from the selected_fields
        fields_json = {
            "aggregation-interval": -1,
            "custom-functions": []
        }

        # set aggregation-interval
        if "agg_interval" in selected_fields and selected_fields["agg_interval"] != '':
            fields_json["aggregation-interval"] = int(
                selected_fields["agg_interval"])

        # set functions
        ok_to_write_provision = True
        try:
            for i in selected_fields:
                # set custom functions
                if i in passing_dict["custom_functions"]:
                    fields_json["custom-functions"].append(i)

                # set aggregate functions
                if "aggFunction" in i:
                    _, name, function = i.split("^")
                    if name in fields_json:
                        fields_json[name].append(function)
                    else:
                        fields_json[name] = [function]

        except Exception as err:
            ok_to_write_provision = False
            messages.error(request, f"Request failed with error: {err}")

        # write to provision file
        if ok_to_write_provision:
            write_provision_to_file(request, aggregator_obj, fields_json)

    return render(request, "index.html", passing_dict)


def write_provision_to_file(request, aggregator_obj, fields):
    """
    writes the selected info to provision_file
    """

    provision_file = "provision.json"

    try:
        aggregator_obj.cloud_storage_object.upload_file(
            provision_file, json.dumps(fields, indent=4).encode("utf-8")
        )
        messages.success(request, f"updated provision file: {provision_file}")

    except Exception as err:
        messages.error(
            request, f"failed updating provision file: {provision_file}, Error: {err}")
