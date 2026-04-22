FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir paho-mqtt

COPY mqtt_publisher.py .
COPY edge_ai.py .

CMD ["python", "edge_ai.py"]
