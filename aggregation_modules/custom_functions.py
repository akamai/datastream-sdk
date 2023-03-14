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
defines all custom functions to aggregate the data
New custom functions can to be added here
"""
import json
import logging
import os
import time
import pandas as pd

import httpagentparser

logger = logging.getLogger(__name__)


def convert_time(epoch_time, time_format="%s", delta=1):
    """
    Converts GMT epoch time to the specified time format.
    Also rounds off to the nearest minute, hour, day when valid delta value is passed
    :param epoch_time: epoch time to be converted
    :param time_format: expected output time format
                         example: "%Y-%m-%d %H:%M:%S", "%s", ...
    :param delta: in seconds to be rounded off.
                  example: 300, 1800, 3600...
    :rtype: time
    example:
        >>> epoch_time = "1541399309.143"
        >>> convert_time(epoch_time)
        '1541399309'
        >>> convert_time(epoch_time, time_format="%Y-%m-%d %H:%M:%S %Z")
        '2018-11-05 06:28:29 UTC'
        >>> convert_time(epoch_time, time_format="%Y-%m-%d %H:%M:%S %Z", delta=300)
        '2018-11-05 06:25:00 UTC'
        >>> convert_time(epoch_time, delta=300)
        '1541399100'
    """
    os.environ["TZ"] = "UTC"
    time.tzset()
    # reset delta if unexpected value
    if delta <= 0:
        delta = 1
    # round off the epoch to specified delta
    epoch_rounded = float(epoch_time) - (float(epoch_time) % delta)
    # return in GMT format
    return time.strftime(time_format, time.gmtime(float(epoch_rounded)))


def convert_to_numeric(input_df):
    return pd.to_numeric(input_df, errors='coerce').fillna(0)


def replace_string(input_df, from_str, to_str):
    return input_df.replace(from_str, to_str)


def cal_base_aggregates(lst, input_df):
    """
    Used to calculate basic aggregations
    sum(), min(), max(), mean(), median(), any(), count()
    """
    out = 0
    if lst == "sum":
        out = input_df.sum()
    if lst == "min":
        out = input_df.min()
    if lst == "max":
        out = input_df.max()
    if lst == "mean":
        out = input_df.mean()
    if lst == "median":
        out = input_df.median()
    if lst == "variance":
        out = input_df.var()
    if lst == "any":
        out = input_df.any()
    if lst == "count":
        out = input_df.count()
    return float(out)


def get_unique_counts_of_column(input_df) -> dict:
    """
    returns json formatted output of
    distinct counts of the input dataframe column
    """
    buffer = input_df.value_counts()
    return json.loads(buffer.to_json())


def get_status_code_fillers():
    """
    init new record for status_code statistics
    :rtype: dict
    """
    # Initialize the dictionary
    list_keys = [
        "hits_2xx",
        "hits_3xx",
        "hits_4xx",
        "hits_5xx",
    ]
    return dict.fromkeys(list_keys, 0)


def get_status_code_level_hit_counts(status_code_df):
    """
    returns hits_{2,3,4,5}xx
    sample output,
    ```
        "hits_2xx": 25,
        "hits_3xx": 1,
        "hits_4xx": 1,
        "hits_5xx": 2,
    ```
    """

    mdata = get_status_code_fillers()
    uniq_status_code_counts = get_unique_counts_of_column(status_code_df)
    for status_code, st_count in uniq_status_code_counts.items():
        status_code_prefix = int(int(status_code) / 100)
        if status_code_prefix in [2, 3, 4, 5]:
            mdata["hits_" + str(status_code_prefix) + "xx"] += st_count

    return mdata


def get_traffic_volume(totalbytes_df):
    """
    sum of totalbytes column
    sample output,
    ```
      "traffic_volume": 97230,
    ```
    """
    return int(totalbytes_df.sum())


def cal_cache_status(cache_df):
    """
    returns dict;
    calculates total cache hits and miss
    sample output,
    ```
    {
      "cache_hit": 1,
      "cache_miss": 0,
    }
    ```
    """
    uniq_cache_counts = get_unique_counts_of_column(cache_df)
    cache = {}
    cache["cache_hit"] = uniq_cache_counts.get("1", 0)
    cache["cache_miss"] = uniq_cache_counts.get("0", 0)
    return cache


def cal_offload_rate(cache_df):
    """
    calculates offload rate as,
    total cache hits * 100 / total hits
    sample output,
    ```
      "offload_rate": 80.0,
    ```
    """
    return cache_df[cache_df == 1].sum() * 100.00 / cache_df.count()


def cal_origin_responsetime(dfs):
    """
    calculates origin_responsetime as,
    sum("turnaroundtimemsec")
    where cachestatus == 0 and cacherefreshsrc == 'origin'
    sample output,
    ```
      "origin_response_time": 0,
    ```
    """
    return int(
        dfs.query("cachestatus == 0 and cacherefreshsrc == 'origin'")[
            "turnaroundtimemsec"
        ].sum()
    )


def extract_from_ua(ua_string, to_extract):
    """
    extracts requested info from User Agent String
    """
    client_info = httpagentparser.detect(ua_string)
    if to_extract in client_info:
        if client_info[to_extract]["name"] is not None:
            return client_info[to_extract]["name"]
    return str("invalid")


def parse_user_agent(user_agent):
    """
    returns platform, os, browser distribution details.
    sample output,
    ```
    "platform": {
      "Windows": 30
    },
    "os": {
      "Windows": 30
    },
    "browser": {
      "Chrome": 30
    }
    ```
    """
    ua_info = (
        "os",
        "browser",
        "platform",
    )
    client_info = {}
    for to_extract in ua_info:
        client_info[to_extract] = user_agent.apply(
            extract_from_ua, args=(to_extract,))
        # convert to json
        client_info[to_extract] = json.loads(
            client_info[to_extract].value_counts().to_json()
        )
    return client_info


def parse_unique_count_for_column(column_df, column):
    """
    returns column specific distribution details.
    sample output,
    ```
    "<column_df>": {
      "<>": 30
    }
    ```
    """

    return {column: get_unique_counts_of_column(column_df)}


def calc_unique_visitor(dfs):
    """
    returns total number of unique visitor     calculation should be done based on Client IP and UserAgent.
    :param dfs:
    :return: unique_visitors_value: [(user_agent, client_ip)]
    """
    result = {}
    unique_visitors = set()
    if dfs is not None:
        for user_agent, client_ip in dfs.itertuples(index=False):
            if (user_agent, client_ip) not in unique_visitors:
                unique_visitors.add((user_agent, client_ip))
        result["unique_visitors_value"] = list(unique_visitors)
        return result
