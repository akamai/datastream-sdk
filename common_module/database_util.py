import logging
import os
import azure.cosmos.cosmos_client as cosmos_client


def get_cosmos_db_connection():
    cosmos_db_end_point = os.environ["COSMOS_DB_ENDPOINT"]
    cosmos_db_primary_key = os.environ["COSMOS_DB_PRIMARY_KEY"]
    cosmos_db_database_name = os.environ["COSMOS_DATABASE_NAME"]
    cosmos_db_container_name = os.environ["COSMOS_CONTAINER_NAME"]

    logging.debug(
        f"cosmos_db_end_point:{cosmos_db_end_point}\n"
        f"cosmos_db_primary_key: {cosmos_db_primary_key}\n"
        f"cosmos_db_database_name: {cosmos_db_database_name}\n"
        f"cosmos_db_container_name: {cosmos_db_container_name}")

    auth = {"masterKey": cosmos_db_primary_key}
    client = cosmos_client.CosmosClient(cosmos_db_end_point, auth)
    database = client.get_database_client(cosmos_db_database_name)
    container = database.get_container_client(cosmos_db_container_name)
    return container


def get_athena_db_connection():
    return ""


def db_connection(database_type):
    if database_type == "cosmos":
        return get_cosmos_db_connection()
    elif database_type == "athena":
        return get_athena_db_connection()
    else:
        raise Exception("Error: invalid database type")

