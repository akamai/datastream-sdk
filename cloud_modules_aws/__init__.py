import json
import logging

import run_aggregations


def lambda_handler(event, context):
    logging.getLogger().setLevel(logging.INFO)
    result = run_aggregations.main(event, None, cloud="aws")
    logging.info(json.dumps(result, indent=2))
    return result
