import paho.mqtt.client as mqtt
import json, time, random, math

BROKER = "172.31.48.1"
TOPIC  = "sensors/group11/temperature/data"

client = mqtt.Client()
client.connect(BROKER, 1883, 60)

print("🚀 Simulation started! Sending data every 3 seconds...")
t = 0
while True:
    # Normal room temperature with variation
    base = 26 + 3 * math.sin(t / 20)
    noise = random.uniform(-0.5, 0.5)
    temp = base + noise

    # Inject anomaly 5% of the time
    if random.random() < 0.05:
        temp += random.uniform(8, 15)
        print("💥 Anomaly injected!")

    payload = json.dumps({
        "temperature": round(temp, 1),
        "humidity": round(50 + random.uniform(-5, 5), 1),
        "timestamp": time.time()
    })

    client.publish(TOPIC, payload)
    print(f"📤 Sent: {payload}")
    t += 1
    time.sleep(3)