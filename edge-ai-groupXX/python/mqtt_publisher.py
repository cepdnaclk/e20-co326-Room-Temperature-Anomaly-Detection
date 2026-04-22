"""
mqtt_publisher.py
Simulates room temperature data with an HVAC-driven sine wave pattern,
Gaussian noise, and periodic spike anomalies. Publishes readings to the
MQTT broker on the topic room/temperature.
"""

import time
import math
import random
import json
import paho.mqtt.client as mqtt

# ── MQTT configuration ─────────────────────────────────────────────────────────
BROKER_HOST = "mosquitto"
BROKER_PORT = 1883
TOPIC_TEMPERATURE = "room/temperature"

# ── Simulation parameters ──────────────────────────────────────────────────────
BASE_TEMP        = 22.0   # °C  – midpoint of the HVAC cycle
HVAC_AMPLITUDE   = 3.0    # °C  – half-range of the sine wave
HVAC_PERIOD      = 300    # s   – full HVAC cycle period (5 min)
NOISE_STD        = 0.4    # °C  – standard deviation of Gaussian noise
SPIKE_PROB       = 0.03   # probability of a spike anomaly per sample
SPIKE_MAGNITUDE  = 15.0   # °C  – magnitude added during a spike
PUBLISH_INTERVAL = 2      # s   – seconds between samples


def create_client(broker: str, port: int) -> mqtt.Client:
    client = mqtt.Client(client_id="temp_publisher")
    client.connect(broker, port, keepalive=60)
    return client


def simulate_temperature(t: float) -> tuple[float, bool]:
    """
    Return (temperature, is_spike) for time *t* (seconds since start).

    Normal behaviour: BASE_TEMP + HVAC sine wave + Gaussian noise.
    Anomaly:          add a large positive spike with probability SPIKE_PROB.
    """
    hvac   = HVAC_AMPLITUDE * math.sin(2 * math.pi * t / HVAC_PERIOD)
    noise  = random.gauss(0, NOISE_STD)
    temp   = BASE_TEMP + hvac + noise

    is_spike = random.random() < SPIKE_PROB
    if is_spike:
        temp += SPIKE_MAGNITUDE

    return round(temp, 2), is_spike


def main() -> None:
    client = create_client(BROKER_HOST, BROKER_PORT)
    client.loop_start()
    print(f"[Publisher] Connected to {BROKER_HOST}:{BROKER_PORT}")

    start = time.time()
    try:
        while True:
            t    = time.time() - start
            temp, spike = simulate_temperature(t)

            payload = json.dumps({
                "temperature": temp,
                "timestamp":   time.time(),
                "spike":       spike,
            })

            client.publish(TOPIC_TEMPERATURE, payload)
            print(f"[Publisher] Published {temp:.2f}°C"
                  f"{' *** SPIKE ***' if spike else ''}")

            time.sleep(PUBLISH_INTERVAL)
    except KeyboardInterrupt:
        print("[Publisher] Stopping.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
