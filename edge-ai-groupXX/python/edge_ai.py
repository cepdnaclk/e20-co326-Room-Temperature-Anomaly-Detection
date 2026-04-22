"""
edge_ai.py
Subscribes to room/temperature, detects anomalies using Z-score analysis
and a hard threshold (>35 °C), then publishes structured alerts to
room/temperature/alerts.

Runs the MQTT publisher in a background thread so both components can be
exercised from a single Docker container entry point.
"""

import json
import threading
import time
from collections import deque

import paho.mqtt.client as mqtt

# ── MQTT configuration ─────────────────────────────────────────────────────────
BROKER_HOST       = "mosquitto"
BROKER_PORT       = 1883
TOPIC_TEMPERATURE = "room/temperature"
TOPIC_ALERTS      = "room/temperature/alerts"

# ── Anomaly-detection parameters ───────────────────────────────────────────────
WINDOW_SIZE        = 30     # number of recent readings for rolling statistics
ZSCORE_THRESHOLD   = 3.0    # Z-score magnitude that triggers an alert
TEMP_THRESHOLD     = 35.0   # °C  – hard upper-bound threshold

# ── Rolling statistics window ──────────────────────────────────────────────────
_window: deque[float] = deque(maxlen=WINDOW_SIZE)


def _mean(values: deque) -> float:
    return sum(values) / len(values)


def _std(values: deque) -> float:
    mu  = _mean(values)
    var = sum((x - mu) ** 2 for x in values) / len(values)
    return var ** 0.5


def compute_zscore(temp: float) -> float | None:
    """Return Z-score of *temp* against the current window, or None if the
    window is too small to be meaningful."""
    if len(_window) < 10:
        return None
    mu  = _mean(_window)
    sigma = _std(_window)
    if sigma == 0:
        return 0.0
    return (temp - mu) / sigma


def detect_anomaly(temp: float) -> tuple[bool, str, float | None]:
    """
    Return (is_anomaly, reason, zscore).

    Checks:
      1. Hard threshold  > TEMP_THRESHOLD
      2. Statistical     |Z-score| > ZSCORE_THRESHOLD
    """
    if temp > TEMP_THRESHOLD:
        return True, f"Temperature {temp:.2f}°C exceeds threshold {TEMP_THRESHOLD}°C", None

    z = compute_zscore(temp)
    if z is not None and abs(z) > ZSCORE_THRESHOLD:
        return True, f"Z-score {z:.2f} exceeds threshold ±{ZSCORE_THRESHOLD}", z

    return False, "", z


def on_message(client: mqtt.Client, _userdata, message: mqtt.MQTTMessage) -> None:
    """Callback for incoming temperature messages."""
    try:
        data = json.loads(message.payload.decode())
        temp = float(data["temperature"])
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"[EdgeAI] Bad payload: {exc}")
        return

    is_anomaly, reason, zscore = detect_anomaly(temp)
    _window.append(temp)           # update rolling window *after* detection

    status = "ANOMALY" if is_anomaly else "normal"
    print(f"[EdgeAI] {temp:.2f}°C  [{status}]"
          + (f"  → {reason}" if is_anomaly else ""))

    if is_anomaly:
        alert = json.dumps({
            "temperature": temp,
            "timestamp":   data.get("timestamp", time.time()),
            "reason":      reason,
            "zscore":      zscore,
        })
        client.publish(TOPIC_ALERTS, alert)
        print(f"[EdgeAI] Alert published → {TOPIC_ALERTS}")


def start_publisher() -> None:
    """Launch mqtt_publisher in a background daemon thread."""
    import mqtt_publisher  # local module
    t = threading.Thread(target=mqtt_publisher.main, daemon=True)
    t.start()


def main() -> None:
    # Give the broker a moment to start before connecting
    time.sleep(3)

    client = mqtt.Client(client_id="edge_ai")
    client.on_message = on_message
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.subscribe(TOPIC_TEMPERATURE)
    print(f"[EdgeAI] Subscribed to {TOPIC_TEMPERATURE}")

    # Start the simulator in the background
    start_publisher()

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("[EdgeAI] Stopping.")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
