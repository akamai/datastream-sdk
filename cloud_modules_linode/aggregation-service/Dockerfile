FROM python:3.13-slim

WORKDIR /app

COPY cloud_modules_linode/aggregation_service/requirements.txt ./
COPY requirements.txt ./base-requirements.txt
COPY cloud_modules_aws/requirements.txt ./aws-requirements.txt

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r base-requirements.txt
RUN pip install --no-cache-dir -r aws-requirements.txt

COPY aggregation_modules ./aggregation_modules/
COPY cloud_modules_aws ./cloud_modules_aws/
COPY cloud_modules_linode/aggregation_service/src/* ./

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
