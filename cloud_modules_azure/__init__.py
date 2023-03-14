import logging
import run_aggregations
import json
import os
from common_module.database_util import db_connection
from .common_utils import calculate_delta, create_document, query_item_from_db, update_result, \
    upsert_items_into_cosmos_db
import azure.functions as func


def main(myblob: func.InputStream, resultdoc: func.Out[func.DocumentList]):
    logging.info(
        f"Python blob trigger function processing blob \n"
        f"Name: {myblob.name}\n"
        f"Blob Size: {myblob.length} bytes"
    )

    result = run_aggregations.main(None, myblob, cloud="azure")

    ingest_data(result)

    result = update_result(result)

    logging.info(json.dumps(result, indent=2))

    resultdoc.set(func.DocumentList(result))


def ingest_data(result):
    """

    :param result:
    :return:
    """
    logging.info(f"result:{result}")

    cosmos_db_container_name = os.environ["COSMOS_CONTAINER_NAME"]
    logging.info(f"cosmos_db_container_name: {cosmos_db_container_name}")

    container = db_connection("cosmos")
    upsert_items_into_cosmos_db(container, cosmos_db_container_name, result)
