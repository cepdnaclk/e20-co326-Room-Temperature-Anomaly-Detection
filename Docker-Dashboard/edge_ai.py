import paho.mqtt.client as mqtt
import json

BROKER = "172.31.48.1"
DATA_TOPIC  = "sensors/group11/temperature/data"
ALERT_TOPIC = "alerts/group11/temperature/status/detail"

history = []

def detect_anomaly(temp):
    global history
    history.append(temp)
    if len(history) > 10:
        history.pop(0)
    reasons = []
    if temp > 32.0:
        reasons.append(f"HIGH TEMP: {temp}°C")
    if len(history) >= 3:
        avg = sum(history[:-1]) / len(history[:-1])
        if abs(temp - avg) > 5:
            reasons.append(f"SPIKE: {temp}°C vs avg {avg:.1f}°C")
    return reasons

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        temp = data["temperature"]
        print(f"📥 Temp: {temp}°C")
        anomalies = detect_anomaly(temp)
        if anomalies:
            alert = json.dumps({"status": "ALERT", "reasons": anomalies, "temp": temp})
            client.publish(ALERT_TOPIC, alert)
            print(f"🚨 ALERT sent: {anomalies}")
        else:
            client.publish(ALERT_TOPIC, json.dumps({"status": "NORMAL", "temp": temp}))
            print("✅ Normal")
    except Exception as e:
        print(f"Error: {e}")

client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER, 1883, 60)
client.subscribe(DATA_TOPIC)
print("🤖 Edge AI running...")
client.loop_forever()