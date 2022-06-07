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

"""Helps createing a basic Athena setup in your S3 account

i.e It creates the necessary S3 bucket, Database, Table and
an aggregated View for the data stored in your stream in S3 bucket.
So we can use this table or view to query the data.

usage example:

    python loadtoathena.py
    python loadtoathena.py --dryrun
"""

import argparse
import textwrap
import logging
import json
import re
from typing import Tuple
import boto3
from botocore.exceptions import ClientError


def parse_inputs() -> dict:
    """
    parse the input command line arguments
    and return dictionary
    """

    parser = argparse.ArgumentParser(
        prog="loadtoathena.py",
        formatter_class=argparse.RawTextHelpFormatter,
        description=textwrap.dedent(
            """\
            Helps setting up the athena database, table and view
            that in turn helps to query the Datastream2 logs
            stored in S3 buckets
            """
        ),
    )

    parser.add_argument(
        "--loglevel",
        default="info",
        type=str,
        choices=["critical", "error", "warn", "info", "debug"],
        help=textwrap.dedent(
            """\
            logging level.
            (default: %(default)s)
            \n"""
        ),
    )

    parser.add_argument(
        "--dryrun",
        action="store_true",
        help=textwrap.dedent(
            """\
            shows the commands that will be executed by this script
            without actually running it.
            the default loglevel for this mode is debug.
            (default: %(default)s)
            \n"""
        ),
    )

    parser.add_argument(
        "--log_field_maps",
        default="conf/log_fields.json",
        type=str,
        help=textwrap.dedent(
            """\
            json file with field id to name mapping and aggregate functions.
            (default: %(default)s)
            \n"""
        ),
    )
    parser.add_argument(
        "--formulas_json",
        default="conf/formulas.json",
        type=str,
        help=textwrap.dedent(
            """\
            json file with formulas for the aggregate functions.
            (default: %(default)s)
            \n"""
        ),
    )
    parser.add_argument(
        "--stream_json",
        default="conf/sample_stream.json",
        type=str,
        help=textwrap.dedent(
            """\
            json file with stream details.
            (default: %(default)s)
            \n"""
        ),
    )
    parser.add_argument(
        "--out_bucket",
        default="athena-result-bucket",
        type=str,
        help=textwrap.dedent(
            """\
            output bucket to store athena query results.
            (default: %(default)s-<STREAM_JSON:streamId>)
            \n"""
        ),
    )
    parser.add_argument(
        "--out_bucket_path",
        default="",
        type=str,
        help=textwrap.dedent(
            """\
            output bucket path to store athena query results.
            (default: %(default)s)
            \n"""
        ),
    )
    parser.add_argument(
        "--out_bucket_region",
        type=str,
        help=textwrap.dedent(
            """\
            s3 region for the output bucket that stores query results.
            if not provided, the default region will be parsed from the stream json file.
            (default: STREAM_JSON:connectors["region"]
            \n"""
        ),
        default="",
    )
    parser.add_argument(
        "--db_name",
        default="athena_db",
        type=str,
        help=textwrap.dedent(
            """\
            database name to create.
            (default: %(default)s_<STREAM_JSON:streamId>)
            \n"""
        ),
    )
    parser.add_argument(
        "--table_name",
        default="athena_table",
        type=str,
        help=textwrap.dedent(
            """\
            table name to create.
            (default: %(default)s_<STREAM_JSON:streamId>_<STREAM_JSON:streamVersionId>)
            \n"""
        ),
    )
    parser.add_argument(
        "--view_name",
        default="athena_view",
        type=str,
        help=textwrap.dedent(
            """\
            view name to create.
            (default: %(default)s_<STREAM_JSON:streamId>_<STREAM_JSON:streamVersionId>)
            \n"""
        ),
    )
    parser.add_argument(
        "--workgroup",
        default="athena_workgroup",
        type=str,
        help=textwrap.dedent(
            """\
            The workgroup name to create to execute athena queries.
            In order to store the query results in the provided s3://<out_bucket>/<out_bucket_path>,
            ensure to switch to this workgroup while running queries.
            (default: %(default)s_<STREAM_JSON:streamId>)
            \n"""
        ),
    )

    return vars(parser.parse_args())


def parse_json(file_to_read: str) -> dict:
    """
    Parse a JSON file and returns dict
    """
    json_data = {}
    try:
        with open(file_to_read, "r", encoding="UTF-8") as json_file_reader:
            json_data = json.load(json_file_reader)

    except Exception as err:
        logger.error("parsing failed for json file: %s", file_to_read)
        logger.error(err)
        raise

    return json_data


def remove_prefix(name: str, prefix: str) -> str:
    """
    Returns string removing the prefix
    """
    if name.startswith(prefix):
        return name[len(prefix):]
    else:
        return name[:]


def get_full_path(bucket_name: str, bucket_path: str) -> str:
    """
    Returns the bucket with full path
    """
    dest = "s3://"
    # strip s3:// prefix from the bucket_name if exists
    # if bucket _name contains any leading or trailing / strip here
    dest += remove_prefix(bucket_name, "s3://").lstrip("/").rstrip("/")
    if bucket_path:
        for lvl in bucket_path.split("/"):
            if "{" in lvl:
                # strip dynamic time variable suffixes
                # and anything after them from the path if exists
                break
            if lvl:
                dest += "/" + lvl
    # now we are good to add the trailing slash here
    dest += "/"
    return dest


def get_input_data_spec(stream_data_set: dict) -> Tuple[str, str]:
    """
    Returns the input data format and delimiter
    """

    # STRUCTURED or JSON
    data_format = stream_data_set["format"]
    delimiter = None

    # check for custom delimiters
    if stream_data_set["delimiter"] == "SPACE":
        delimiter = repr(" ")

    # Add a slash before the escape character
    # say \t to \\t
    if stream_data_set["delimiter"] == "TAB":
        delimiter = repr("\\" + "t")

    return data_format, delimiter


def get_datasetids(stream_datasets) -> list:
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


def get_rslt_config(bucket_name: str, bucket_path: str) -> dict:
    """
    Returns the ResultConfiguration used by start_query_execution module
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/athena.html#Athena.Client.start_query_execution

    Example:
    ```
        ResultConfiguration = {
            'OutputLocation': 'string',
            'EncryptionConfiguration': {
                'EncryptionOption': 'SSE_S3'|'SSE_KMS'|'CSE_KMS',
                'KmsKey': 'string'
            }
    ```
    """

    rslt_config = {}
    rslt_config["OutputLocation"] = get_full_path(bucket_name, bucket_path)

    # we can setup the EncryptionConfiguration here that
    # can be used to encrupt the Query Results.
    # This is a client-side setting.
    # Workgroup Settings Override Client-Side Settings
    # https://docs.aws.amazon.com/athena/latest/ug/workgroups-settings-override.html
    # rslt_config["EncryptionConfiguration"] = {
    #     "EncryptionOption": "SSE_S3" | "SSE_KMS" | "CSE_KMS",
    #     "KmsKey": "string",
    # }

    return rslt_config


def create_iam_user(iamclient, user_name):
    """
    creates an IAM user
    """
    # TODO:
    # check if this is needed
    # and to be improved accordingly
    try:
        user = iamclient.create_user(
            UserName=user_name,
            Tags=[
                {"Key": "email", "Value": "testuser@test.com"},
                {"Key": "description", "Value": "Test for Athena load"},
            ],
        )
        logger.info("user %s created successfully", user_name)
        return user
    except Exception as err:
        logger.warning(err)
        raise


def attach_policy_to_user(iamclient, user_name, policy_arn):
    """
    Attaches a policy to a user.
    :param user_name: The name of the user.
    :param policy_arn: The Amazon Resource Name (ARN) of the policy.
    """
    # TODO:
    # check if this is needed
    # and to be improved accordingly
    try:
        iamclient.User(user_name).attach_policy(PolicyArn=policy_arn)
        logger.info("Attached policy %s to user %s.", policy_arn, user_name)
    except ClientError:
        logger.warning("Couldn't attach policy %s to user %s.",
                       policy_arn, user_name)
        raise


def create_datacatalog(glue_client):
    """
    used to create a data catalog
    """
    # TODO:
    # check if this is needed
    # and to be improved accordingly
    response = glue_client.create_data_catalog(
        Name="string",
        Type="LAMBDA" | "GLUE" | "HIVE",
        Description="Test catalog",
        Parameters={"string": "string"},
        Tags=[
            {"Key": "string", "Value": "string"},
        ],
    )

    return response


def create_s3_bucket(dryrun: bool, bucket_name: str, bucket_region: str) -> None:
    """
    Create a bucket.
    If the bucket already exists and you have access to it, no bucket will be created.

    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Bucket.create
    """

    logger.info("creating bucket %s in region %s", bucket_name, bucket_region)

    if dryrun:
        logger.info("in dry run mode.. not running!")
        return

    response = ""

    # check if the bucket exists and we have access to it or None.
    try:
        # To create bucket in the specified region
        s3client = boto3.client("s3", region_name=bucket_region)
        response = s3client.head_bucket(Bucket=bucket_name)
        logger.info("bucket exists.. not creating")

    except ClientError as err:
        logger.info("lookup on bucket failed with error: %s", err)
        logger.info("bucket doesn't exist, creating...")

        # Let's try to create the bucket. This will fail if
        # the bucket has already been created by someone else.
        try:

            if bucket_region == "us-east-1":
                response = s3client.create_bucket(
                    Bucket=bucket_name, ACL="private")
            else:
                response = s3client.create_bucket(
                    Bucket=bucket_name,
                    ACL="private",
                    CreateBucketConfiguration={
                        "LocationConstraint": bucket_region},
                )
            logger.info(
                "Response Code: %s", response["ResponseMetadata"]["HTTPStatusCode"]
            )

        except ClientError as err:
            logger.warning("failed creating bucket...")
            logger.warning(err)
            raise

    if response:
        logger.debug("response...\n%s", json.dumps(response, indent=2))


def execute_query(
    dryrun: bool,
    bucket_region: str,
    query_str: str,
    rslt_config: dict,
    query_exec_context=None,
) -> None:
    """
    Runs the Specified Query in Athena using start_query_execution service

    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/athena.html#Athena.Client.start_query_execution
    """

    if query_exec_context is None:
        query_exec_context = {}

    logger.debug("executing query...\n\n%s\n", query_str)
    logger.debug(
        "with query execution context...\n%s", json.dumps(
            query_exec_context, indent=2)
    )
    logger.debug("with result configuration...\n%s",
                 json.dumps(rslt_config, indent=2))

    if dryrun:
        logger.debug("in dry run mode.. not running!")
        return

    response = ""
    try:

        athenaclient = boto3.client("athena", region_name=bucket_region)

        # ClientRequestToken = "string"
        response = athenaclient.start_query_execution(
            QueryString=query_str,
            ResultConfiguration=rslt_config,
            QueryExecutionContext=query_exec_context,
        )
        logger.info("response code: %s",
                    response["ResponseMetadata"]["HTTPStatusCode"])

    except ClientError as err:
        logger.warning("Failed executing statement")
        logger.warning(err)
        raise

    if response:
        logger.debug("response...\n%s", json.dumps(response, indent=2))


def create_athena_database(
    dryrun: bool, bucket_region: str, db_name: str, rslt_config: dict
) -> None:
    """
    Creates the database if it doesn't exists in Athena
    """

    logger.info("creating database: %s", db_name)
    # Construct create database string
    query_str = f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
    query_str += "\n  COMMENT 'Database to store Athena query results'"

    query_exec_context = {"Catalog": "AwsDataCatalog"}
    execute_query(dryrun, bucket_region, query_str,
                  rslt_config, query_exec_context)


def get_fields_with_datatype(
    dataset_ids: list, field_info: dict, data_format: str
) -> dict:
    """
    Returns the column name and its data type by looking up stream and log_fields json file.

    If a mapping column name is not present in log_fields.json it returns
    the column name as `col<idx>` and its data type as `string`

    Example:
    ```
    {
        "cp": "string",
        "bytes" : "bigint",
        "col1": "string"
    }
    ```
    """

    result = {}
    result["version"] = "string"
    # start set as 1 as the 0th field is version
    # if the column name lookup on field_info fails,
    # it sets the column name as col<idx> ex, col5
    # for JSON, column format is string by default
    for itr, colid in enumerate(dataset_ids, start=1):
        result[field_info.get(colid, {"name": "col" + str(itr)})["name"]] = (
            "string"
            if data_format == "JSON"
            else field_info.get(colid, {"dtype": "string"})["dtype"]
        )

    return result


def get_table_cols(dataset_ids: list, field_info: dict, data_format: str) -> str:
    """
    returns the formatted table columns to be used in select statement.

    Example:
    ```
        `version` string,
        `cp` string,
        `reqId` string,
    ```
    """

    col_to_dtype = get_fields_with_datatype(
        dataset_ids, field_info, data_format)
    result = ",\n ".join(f"`{k}` {v}" for k, v in col_to_dtype.items())
    return result


def construct_query(params: dict, field_info: dict) -> str:
    """
    returns the formatted create table statement.
    """

    query_str = "CREATE EXTERNAL TABLE IF NOT EXISTS "
    # concatenate table name
    query_str += f'`{params["db_name"]}`.`{params["table_name"]}` ('
    # concatenate table columns
    query_str += "\n "
    query_str += get_table_cols(
        params["input"]["datasetids"], field_info, params["input"]["data_format"]
    )
    query_str += " \n)"

    # set ROW FORMAT
    if params["input"]["data_format"] == "CSV":
        # https://docs.aws.amazon.com/athena/latest/ug/csv-serde.html
        query_str += "\nROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'"
        query_str += "\nWITH SERDEPROPERTIES ("
        # space-seperated
        query_str += "\n    'separatorChar' = ',',"
        # double quoted strings
        query_str += "\n    'quoteChar' = '\"', "
        # escape charater: \\
        query_str += "\n    'escapeChar' = '\\\\' )"

    if params["input"]["data_format"] == "JSON":
        query_str += "ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'"

    if params["input"]["data_format"] == "STRUCTURED":
        query_str += "\nROW FORMAT DELIMITED"
        # custom delimiter
        query_str += f'\n    FIELDS TERMINATED BY {params["input"]["data_delimiter"]}'
        # escape charater: \\
        query_str += "\n    ESCAPED BY '\\\\'"
        # lines
        query_str += "\n    LINES TERMINATED BY '\\n'"

    # set storage format
    query_str += "\nSTORED AS"
    query_str += "\n    INPUTFORMAT 'org.apache.hadoop.mapred.TextInputFormat'"
    query_str += "\n    OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'"

    # set input location
    query_str += f'\nLOCATION \'{params["input"]["bucket_path"]}\''

    return query_str


def create_athena_table(params: dict, field_info: dict) -> None:
    """
    Creates the table if it doesn't exist in Athena
    """

    logger.info("creating table: `%s`.`%s`",
                params["db_name"], params["table_name"])
    query_exec_context = {
        "Database": params["db_name"],
        "Catalog": params["catalog_name"],
    }

    execute_query(
        params["dryrun"],
        params["out_bucket_region"],
        construct_query(params, field_info),
        params["rslt_config"],
        query_exec_context,
    )


def extract_agg_functions(
    dataset_ids: list, field_info: dict, formulas: dict, data_format: str
) -> dict:
    """
    returns the subset of aggregated functions for the selected datasets

    Example:
    ```
        {
            "bytesPerSecond" : "avg(bytes)",
            "1xx": "sum(case when statusCode / 100 = 1 then 1 else 0 end)",
        }
    ```
    """
    result = {}

    for col in dataset_ids:
        # skip if the column doesn't have any
        # aggregate functions
        if "agg" not in field_info.get(col, {}):
            continue

        for func_name in field_info[col]["agg"]:
            # initialize a flag here
            # this flag is used to validate if this function
            # has any dependent columns and checks if the
            # dependent columns are part of the selected dataset
            toadd_flag = True

            # skip if the function is not defined
            if func_name not in formulas["functions"]:
                continue

            query = formulas["functions"][func_name].get("q", None)
            # skip if no query is defined for the function
            if query is None:
                continue

            # check if the function has any dependent columns
            if "dependent_cols" in formulas["functions"].get(func_name):
                for idx, dep_col in enumerate(
                    formulas["functions"][func_name]["dependent_cols"]
                ):
                    # reset this flag to True for every function
                    toadd_flag = True
                    # check if the dependent columns are
                    # part of the selected dataset
                    if dep_col in dataset_ids:
                        if data_format == "STRUCTURED":
                            query = query.replace(
                                "_var" + str(idx) +
                                "_", field_info[dep_col]["name"]
                            )

                        if data_format == "JSON":
                            # if string, convert to varchar
                            query = query.replace(
                                "_var" + str(idx) + "_",
                                "CAST("
                                + field_info[dep_col]["name"]
                                + " as "
                                + "varchar"
                                if field_info[dep_col]["dtype"] == "string"
                                else field_info[dep_col]["dtype"] + ")",
                            )
                    else:
                        # this means one or more of the dependent columns
                        # are not part of the selected dataset
                        toadd_flag = False

            if toadd_flag:
                if data_format == "STRUCTURED":
                    result[func_name] = query.replace(
                        "_var_", field_info[col]["name"])

                if data_format == "JSON":
                    # if string, convert to varchar
                    result[func_name] = query.replace(
                        "_var_",
                        "CAST(" + field_info[col]["name"] + " as " + "varchar"
                        if field_info[col]["dtype"] == "string"
                        else field_info[col]["dtype"] + ")",
                    )

    # other aggregate functions
    # other functions is presumed to not have any dependent columns
    for func_name in field_info["others"]["agg"]:
        result[func_name] = formulas["functions"][func_name]["q"]

    return result


def construct_aggregated_query(params: dict, field_info: dict, formulas: dict) -> str:
    """
    constructs the create view statement
    """

    # create view <dbname>.<viewname> as
    query_str = "CREATE OR REPLACE VIEW "
    query_str += f'"{params["db_name"]}"."{params["view_name"]}" AS'

    # select <columns>
    # add direct dimensions to select
    grp_by_cols = set()
    for grp_id in formulas["dimension"]["direct"]:
        grp_by_cols.add(f'"{field_info[grp_id]["name"]}"')

    query_str += "\n SELECT {} ".format(",\n ".join(grp_by_cols))

    # add derived dimensions to select
    agg_funcs = extract_agg_functions(
        params["input"]["datasetids"],
        field_info,
        formulas,
        params["input"]["data_format"],
    )

    for idx, func_name in enumerate(
        formulas["dimension"]["derived"], start=(len(grp_by_cols) + 1)
    ):
        query_str += f',\n  {agg_funcs.get(func_name)} as "{func_name}"'
        # add to group by columns
        grp_by_cols.add(str(idx))

    for col_key, col_val in agg_funcs.items():
        if col_key not in formulas["dimension"]["derived"]:
            query_str += f',\n  {col_val} as "{col_key}"'

    # from <db>.<table>
    query_str += f'\n FROM "{params["db_name"]}"."{params["table_name"]}"'

    # group by <columns>
    query_str += f'\n GROUP BY {", ".join(grp_by_cols)}'

    return query_str


def create_athena_view(params: dict, field_info: dict, formulas: dict) -> None:
    """
    Creates the view in Athena if it doesn't exists
    """

    logger.info('creating view: "%s"."%s"',
                params["db_name"], params["view_name"])
    query_exec_context = {
        "Database": params["db_name"],
        "Catalog": params["catalog_name"],
    }

    execute_query(
        params["dryrun"],
        params["out_bucket_region"],
        construct_aggregated_query(params, field_info, formulas),
        params["rslt_config"],
        query_exec_context,
    )


def create_athena_work_group(
    dryrun: bool, bucket_region: str, rslt_config: dict, wrk_grp: str
) -> None:
    """
    Creates a workgroup with the specified name using create_work_group service

    Reference,
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/athena.html#Athena.Client.create_work_group
    """

    logger.info("creating workgroup %s to run athena queries", wrk_grp)
    logger.debug("with result configuration...\n%s",
                 json.dumps(rslt_config, indent=2))

    if dryrun:
        logger.debug("in dry run mode.. not running!")
        return

    response = ""
    try:

        athenaclient = boto3.client("athena", region_name=bucket_region)
        response = athenaclient.get_work_group(WorkGroup=wrk_grp)
        logger.info("work group exists.. not creating")

    except ClientError as err:
        # print(response)
        logger.info("lookup on workgroup failed with error: %s", err)
        logger.info("workgroup doesn't exist, creating...")

        try:
            response = athenaclient.create_work_group(
                Name=wrk_grp,
                Configuration={
                    "ResultConfiguration": rslt_config,
                },
                Description="Workgroup to run Athena Queries",
            )
            logger.info(
                "response code: %s", response["ResponseMetadata"]["HTTPStatusCode"]
            )

        except ClientError as err:
            logger.warning("Failed creating workgroup")
            logger.warning(err)
            raise

    if response:
        logger.debug("response...\n%s", json.dumps(
            response, indent=2, default=str))


def main() -> None:
    """
    main function
    """

    ##########################################
    # commenting this section as it requires #
    # special permissions to set this up     #
    ##########################################
    # test_user = "test_user_1"
    # iamclient = boto3.resource("iam")
    # # Create IAM user
    # create_iam_user(iamclient, test_user)

    # # Attach the Policy ARNs to the IAM user
    # policy_arns = {
    #     "s3fullaccess": "arn:aws:iam::aws:policy/AmazonS3FullAccess",
    #     "athenafullaccess": "arn:aws:iam::aws:policy/AmazonAthenaFullAccess",
    # }

    # for _, policy_arn in policy_arns.items():
    #     logger.info("provisioning {} to user {}".format(policy_arn, test_user))
    #     attach_policy_to_user(iamclient, test_user, policy_arn)

    logging.basicConfig(
        level=logging.INFO,
        format="%(process)5d| %(asctime)s| %(module)15s:%(lineno)5d| %(levelname)8s| %(message)s",
    )
    log_levels = {
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warn": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
    }

    params = parse_inputs()

    logger.setLevel(log_levels[params["loglevel"]])

    if params["dryrun"]:
        logger.setLevel(logging.DEBUG)
        logger.info("in dry run mode.. loglevel switched to debug mode")

    logger.info("starting...")

    params["catalog_name"] = "AwsDataCatalog"

    # https://developer.akamai.com/api/core_features/datastream2_config/v1.html#gettemplatename
    field_info = parse_json(params["log_field_maps"])
    # https://developer.akamai.com/api/web_performance/datastream/v1.html#getaggregatelogs
    formulas = parse_json(params["formulas_json"])
    # https://developer.akamai.com/api/core_features/datastream2_config/v1.html#getstream
    stream_info = parse_json(params["stream_json"])

    # regex to check if db, table, view and workgroup names are valid
    regex = re.compile(r"[@#!$%^&*()\/|}{~:;[-]")

    # Add streamId to the suffix
    params["out_bucket"] += "-" + str(stream_info.get("streamId", "00000"))

    # Add streamId to the suffix
    for pkey in ["db_name", "workgroup"]:
        if regex.search(params[pkey]) is None:
            params[pkey] += "_" + str(stream_info.get("streamId", "00000"))
        else:
            logger.warning("%s has special characters.", pkey)
            logger.warning(
                "Subsequent DDL or DML queries that reference them can fail."
            )

    # Add streamId_streamVersionId to the suffix
    for pkey in ["table_name", "view_name"]:
        if regex.search(params[pkey]) is None:
            params[pkey] += "_" + str(stream_info.get("streamId", "00000"))
            params[pkey] += "_" + str(stream_info.get("streamVersionId", "1"))
        else:
            logger.warning("%s has special characters.", pkey)
            logger.warning(
                "Subsequent DDL or DML queries that reference them can fail."
            )

    params["input"] = {}

    # It is currently assumed that we will be having one connector per stream
    for con_info in stream_info["connectors"]:
        # Get the input bucket_path from stream json
        if con_info["connectorType"] == "S3":
            params["input"]["bucket_path"] = get_full_path(
                con_info.get("bucket"), con_info.get("path")
            )

        # Get the out bucket region if not specified
        if params["out_bucket_region"] == "":
            params["out_bucket_region"] = con_info.get("region")

    # Get the input data format and its delimiter from stream json
    (
        params["input"]["data_format"],
        params["input"]["data_delimiter"],
    ) = get_input_data_spec(stream_info["config"])

    params["input"]["datasetids"] = get_datasetids(stream_info["datasets"])

    params["rslt_config"] = get_rslt_config(
        params["out_bucket"], params["out_bucket_path"]
    )

    # create modules
    create_s3_bucket(
        params["dryrun"], params["out_bucket"], params["out_bucket_region"]
    )
    # create DB
    create_athena_database(
        params["dryrun"],
        params["out_bucket_region"],
        params["db_name"],
        params["rslt_config"],
    )

    # create table
    create_athena_table(params, field_info)

    # create view
    if params["table_name"] == params["view_name"]:
        logger.warning(
            "Table name and view name provided are the same.Only table will be created."
        )
    else:
        create_athena_view(params, field_info, formulas)

    # create work group
    create_athena_work_group(
        params["dryrun"],
        params["out_bucket_region"],
        params["rslt_config"],
        params["workgroup"],
    )

    logger.info("Finished setting up!")


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    main()
