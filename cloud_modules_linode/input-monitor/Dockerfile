FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src .

RUN mkdir -p /app/configs

CMD ["python", "main.py"]
