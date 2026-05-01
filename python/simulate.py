import paho.mqtt.client as mqtt
import json, time, random, math

BROKER = "mqtt"          # Docker service name
TOPIC  = "sensors/group11/temperature/data"

client = mqtt.Client()

# retry connection
connected = False
while not connected:
    try:
        client.connect(BROKER, 1883, 60)
        connected = True
        print("Connected to MQTT broker!")
    except:
        print("Retrying MQTT connection...")
        time.sleep(3)

print("Simulation started! Sending every 3 seconds...")
t = 0
while True:
    base  = 26 + 3 * math.sin(t / 20)
    noise = random.uniform(-0.5, 0.5)
    temp  = base + noise

    if random.random() < 0.05:
        temp += random.uniform(8, 15)
        print("Anomaly injected!")

    payload = json.dumps({
        "temperature": round(temp, 1),
        "humidity"   : round(50 + random.uniform(-5, 5), 1),
        "timestamp"  : time.time()
    })

    client.publish(TOPIC, payload)
    print(f"Sent: temp={round(temp,1)}C")
    t += 1
    time.sleep(3)