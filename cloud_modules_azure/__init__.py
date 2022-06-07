import logging
import run_aggregations
import json
import azure.functions as func


def main(myblob: func.InputStream, resultdoc: func.Out[func.DocumentList]):

    logging.debug(
        f"Python blob trigger function processing blob \n"
        f"Name: {myblob.name}\n"
        f"Blob Size: {myblob.length} bytes"
    )

    result = run_aggregations.main(None, myblob, cloud="azure")
    logging.debug(json.dumps(result, indent=2))
    resultdoc.set(func.DocumentList(result))
