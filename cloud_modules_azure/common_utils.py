import logging
import datetime
import uuid


def query_item_from_db(container, container_name, logline_date, last_octet, partition_key_value):
    """
    fetch the unique_visitors for given time_stamp from cosmos db
    :param partition_key_value:
    :param last_octet:
    :param logline_date:
    :param container:
    :param container_name:
    :return:
    """
    date_and_octet_query = f"SELECT *  FROM {container_name} c WHERE c.date = '{logline_date}' and c.last_octet = '{last_octet}'"
    octet_query_result = container.query_items(query=date_and_octet_query, partition_key=partition_key_value)
    octet_query_result_as_list = list(octet_query_result)
    return octet_query_result_as_list


def create_document(document_id, partition_key_value, logline_date, last_octet, ua_cip_list_tuple):
    """

    :param document_id:
    :param partition_key_value:
    :param logline_date:
    :param last_octet:
    :param ua_cip_list_tuple:
    :return:
    """
    document = {
        'id': document_id,
        'partition_key': partition_key_value,
        "date": logline_date,
        "last_octet": last_octet,
        "unique_visitor_value": ua_cip_list_tuple
    }
    return document


def update_result(result):
    """
    remove unique_visitors_value from list of dictionary, since we don't require this.
    :param result:
    :return:
    """
    length = len(result)
    logging.info(f"result >> length :{length}")

    for i in range(length):
        del result[i]["unique_visitors_value"]
    return result


def upsert_items_into_cosmos_db(container, container_name, result):
    """
    upsert items into cosmos db, if same time_stamp exist then update the unique visitors and unique_visitors_value
    :param container:
    :param container_name:
    :param result:
    :return:
    """
    length = len(result)
    for i in range(length):

        unique_visitors_value = result[i].get("unique_visitors_value")
        logline_date = datetime.datetime.fromtimestamp(result[i].get("start_timestamp")).date().isoformat()

        for item in unique_visitors_value:
            user_agent = item[0]
            client_ip = item[1]
            last_octet = client_ip.split('.')[-1]
            partition_key_value = logline_date + '_' + last_octet
            ua_cip_list_tuple = [(user_agent, client_ip)]

            query_as_list = query_item_from_db(container, container_name, logline_date,
                                               last_octet, partition_key_value)

            if len(query_as_list) == 0:
                document_id = str(uuid.uuid4())
                logging.info(f"document id >>  :{document_id}")
                document = create_document(document_id, partition_key_value, logline_date, last_octet,
                                           ua_cip_list_tuple)
                container.create_item(body=document, partition_key=partition_key_value)
            else:
                unique_visitor_value_list = query_as_list[0]["unique_visitor_value"]
                delta_list = calculate_delta(unique_visitor_value_list, ua_cip_list_tuple)
                if delta_list is not None and len(delta_list) > 0:
                    unique_visitor_value_list.extend(delta_list)
                    document = create_document(query_as_list[0]["id"], query_as_list[0]["partition_key"],
                                               logline_date, last_octet,
                                               unique_visitor_value_list)
                    container.upsert_item(body=document, partition_key=partition_key_value)


def calculate_delta(existing_unique_visitor_list, current_unique_visitor_list):
    """
    calculate delta from current unique visitors list
    :param existing_unique_visitor_list:
    :param current_unique_visitor_list:
    :return:
    """
    logging.info("calculating delta ::")
    existing_unique_visitor_list = [tuple(x) for x in existing_unique_visitor_list]
    current_unique_visitor_set = set(current_unique_visitor_list)
    existing_unique_visitor_set = set(existing_unique_visitor_list)
    delta_set = current_unique_visitor_set - existing_unique_visitor_set
    return list(delta_set)
