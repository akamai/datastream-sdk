import logging
from datetime import datetime, timedelta


def query_item_from_db(container, query):
    """
    fetch the unique_visitor count  for given logline date from cosmos db
    :param query:
    :param container:
    :return:
    """
    logging.info(f"query:{query}")
    octet_query_result = container.query_items(query=query, enable_cross_partition_query=True)
    total_visitor_count = list(octet_query_result)
    if len(total_visitor_count) > 0:
        logging.info(f"total_visitor_count:{total_visitor_count[0]}")
        return total_visitor_count[0]
    else:
        return 0


def get_date_list(from_date, to_date):
    """

    :param from_date:
    :param to_date:
    :return:
    """
    logging.info(f"Get list of date from {from_date} and {to_date}.")

    date_format = "%Y-%m-%d"

    # from_date and to_date cannot be empty
    if not from_date or not to_date:
        raise Exception("Error: from_date and to_date cannot be empty")

    # validate the date format
    try:
        start_date = datetime.strptime(from_date, date_format)
        end_date = datetime.strptime(to_date, date_format)
    except ValueError:
        raise Exception("Error: from_date or to_date has an invalid date format. Please enter the date in the format "
                        "of YYYY-MM-DD.")

    # to_date cannot be less than from_date
    if end_date < start_date:
        raise Exception("Error: to_date cannot be less than from_date")

    # get today's date
    today = datetime.utcnow()

    # to_date cannot be later than today
    if end_date > today:
        raise Exception("Error: to_date cannot be later than today.")

    delta = end_date - start_date
    days_diff = delta.days

    # The difference between the from_date and to_date should not be more than 90 days
    if days_diff > 90:
        raise Exception("Error: The difference between the from_date and to_date should not be more than 90 days.")

    start_day_delta = today - start_date

    # from_date should not more than 90 days old
    if start_day_delta > timedelta(days=90):
        raise Exception("Error: from_date should not more than 90 days old.")

    date_list = []
    while start_date <= end_date:
        date_list.append(start_date.strftime(date_format))
        start_date += timedelta(days=1)

    date_list.reverse()

    logging.info(f"logline date list :: {date_list}")

    return date_list
