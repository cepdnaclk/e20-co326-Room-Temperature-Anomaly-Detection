import paho.mqtt.client as mqtt
import json, time

BROKER = "mqtt"          # Docker service name
TOPIC  = "sensors/group11/temperature/data"

client = mqtt.Client()

# Same 4 scenarios as hardware
scenarios = [
    {"name": "NORMAL - Morning",   "temp": 22.5, "humidity": 55.0, "duration": 10},
    {"name": "NORMAL - Afternoon", "temp": 27.3, "humidity": 62.0, "duration": 10},
    {"name": "SUPER HOT",          "temp": 42.0, "humidity": 80.0, "duration": 10},
    {"name": "SUPER COOL",         "temp": 10.5, "humidity": 30.0, "duration": 10},
]

print("🚀 Simulation started — 4 scenario mode")

while True:
    for scenario in scenarios:
        print(f"\n{'='*40}")
        print(f"📍 Scenario : {scenario['name']}")
        print(f"🌡️  Temp     : {scenario['temp']}°C")
        print(f"💧 Humidity : {scenario['humidity']}%")
        print(f"{'='*40}")

        # Send data every 2 seconds for the duration
        steps = scenario["duration"] // 2
        for i in range(steps):
            # Add tiny noise so chart looks realistic
            import random
            temp = round(scenario["temp"] + random.uniform(-0.3, 0.3), 1)
            hum  = round(scenario["humidity"] + random.uniform(-0.5, 0.5), 1)

            payload = json.dumps({
                "temperature": temp,
                "humidity": hum,
                "timestamp": time.time()
            })

            client.publish(TOPIC, payload)
            print(f"📤 Sent: temp={temp}°C  hum={hum}%")
            time.sleep(2)

    print("\n>>> All 4 scenarios complete — restarting <<<\n")
