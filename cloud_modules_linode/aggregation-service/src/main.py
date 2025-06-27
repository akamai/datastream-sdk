import logging
import sys
import traceback
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from aggregation_service import AggregationService

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

logger = logging.getLogger(__name__)

app = FastAPI()

class FileList(BaseModel):
    files: List[str]

agg_service = AggregationService()

@app.post("/notify-files")
def notify_files(file_list: FileList):
    logger.info(f"Notifying files: {file_list}")
    for filename in file_list.files:
        try:
            agg_service.process_file(filename)
        except Exception as e:
            logger.error(f"Failed processing {filename}:\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Failed processing {filename}: {str(e)}")
    return {"status": "success"}
