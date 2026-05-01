import paho.mqtt.client as mqtt
import json

# This just forwards alerts to Node-RED
# Actual AI runs on ESP32 now!
BROKER      = "mqtt"
ALERT_TOPIC = "alerts/group11/temperature/status"

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    status = data.get("status", "?")
    method = data.get("method", "?")
    temp   = data.get("temp", 0)
    print(f"{status} | {temp}C | {method}")

client = mqtt.Client()
client.connect(BROKER, 1883, 60)
client.subscribe(ALERT_TOPIC)
client.on_message = on_message
print("Monitoring ESP32 alerts...")
client.loop_forever()