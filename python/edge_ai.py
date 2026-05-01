import paho.mqtt.client as mqtt
import json
import statistics

# Configuration
BROKER      = "172.31.48.1"
DATA_TOPIC  = "sensors/group11/temperature/data"
ALERT_TOPIC = "alerts/group11/temperature/status"

# Data Window (Required for Z-Score ML)
history = []

def detect_anomaly(temp):
    global history
    reasons = []

    # 1. UPDATED HARD THRESHOLD: Range Checking
    # This covers Scenario A (Heat) and Scenario C (Cold)
    if temp > 35.0: 
        reasons.append(f"OVERHEAT: {temp}°C")
    elif temp < 15.0: 
        reasons.append(f"UNDERCOOL: {temp}°C")

    # 2. Z-SCORE ML: Sudden Change Detection
    # This covers Scenario B (The sudden jump from 22 to 30)
    if len(history) >= 5:
        mu = statistics.mean(history)
        sigma = statistics.stdev(history)
        
        if sigma > 0:
            # Formula: z = |T_current - mu| / sigma
            z_score = abs(temp - mu) / sigma
            
            if z_score > 3.0: 
                reasons.append(f"STATISTICAL SPIKE (Z:{z_score:.2f})")

    # Update history buffer
    history.append(temp)
    if len(history) > 10:
        history.pop(0)
        
    return reasons

def on_message(client, userdata, msg):
    try:
        # Parse incoming sensor data
        data = json.loads(msg.payload.decode())
        temp = data["temperature"]
        print(f"📥 Incoming -> Temp: {temp}°C | Humidity: {data.get('humidity', 'N/A')}%")

        anomalies = detect_anomaly(temp)

        if anomalies:
            # Trigger 'ANOMALY' status for warning LEDs or Relays
            alert_payload = {
                "status": "ANOMALY",
                "reasons": anomalies,
                "temp": temp
            }
            client.publish(ALERT_TOPIC, json.dumps(alert_payload))
            print(f"🚨 ALERT SENT: {anomalies}")
        else:
            client.publish(ALERT_TOPIC, json.dumps({"status": "NORMAL", "temp": temp}))
            print("✅ Status: Normal")

    except Exception as e:
        print(f"⚠️ Error: {e}")

# Initialize MQTT Client
client = mqtt.Client()
client.on_message = on_message

print(f"🔗 Connecting to {BROKER}...")
client.connect(BROKER, 1883, 60)
client.subscribe(DATA_TOPIC)

print(f"🤖 Edge AI online. Monitoring: {DATA_TOPIC}")
client.loop_forever()