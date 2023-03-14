import logging
import json
import os

from common_module.database_util import db_connection
from .utils import get_date_list, query_item_from_db
import azure.functions as func


def main(request: func.HttpRequest) -> func.HttpResponse:
    logging.info(
        f"Unique visitor function will get trigger on http request"
    )

    try:
        req_body = request.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON request body", status_code=400)

    # Check if from_date key is present in the request body
    from_date = req_body.get("from_date")
    if not from_date:
        return func.HttpResponse("Request body should contain 'from_date'", status_code=400)

    # Check if to_date key is present in the request body
    to_date = req_body.get("to_date")
    if not to_date:
        return func.HttpResponse("Request body should contain 'to_date'", status_code=400)

    try:
        date_list = get_date_list(from_date, to_date)
    except Exception as e:
        return func.HttpResponse(str(e), status_code=400)

    result = calc_unique_visitor(date_list)
    json_str = json.dumps(result)
    return func.HttpResponse(json_str, mimetype="application/json")


def calc_unique_visitor(date_list):
    """
    :param date_list:
    :return:
    """
    cosmos_db_container_name = os.environ["COSMOS_CONTAINER_NAME"]
    logging.debug(f"cosmos_db_container_name: {cosmos_db_container_name}")

    container = db_connection("cosmos")

    return get_result(container, cosmos_db_container_name, date_list)


def get_result(container, container_name, logline_date_list):
    """

    :param container:
    :param container_name:
    :param logline_date_list:
    :return:
    """
    response = {}
    logging.info(f"Get unique visitor for given dates:: {logline_date_list}")

    for logline_date in logline_date_list:
        # query = f"SELECT DISTINCT CONCAT(val[0],',',val[1]) FROM {container_name} c JOIN val IN
        # c.unique_visitor_value WHERE c.date = '{logline_date}'"

        query = f"select value count(1) from {container_name} c join (SELECT DISTINCT CONCAT(val[0], ',', val[1]) " \
                f"FROM  c JOIN val IN c.unique_visitor_value WHERE c.date = '{logline_date}')"

        count = query_item_from_db(container, query)
        response[logline_date] = count

    return response
