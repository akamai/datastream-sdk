FROM python:3.13-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src .

RUN mkdir -p /app/configs
RUN chown -R appuser:appuser /app

USER appuser

CMD ["python", "main.py"]
