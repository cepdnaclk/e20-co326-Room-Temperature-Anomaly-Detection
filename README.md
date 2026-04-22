# Room Temperature Anomaly Detection – Edge AI IoT System

An end-to-end IoT pipeline that continuously monitors room temperature, detects anomalies using Z-score statistics and a hard threshold, and triggers physical actuators (relay + LEDs) on an ESP32-S3 node.

---

## System Architecture

```
 ┌──────────────────────────────────────────────────────────────────┐
 │                        Docker Host (PC / SBC)                     │
 │                                                                    │
 │  ┌──────────────┐   room/temperature   ┌────────────────────────┐ │
 │  │ mqtt_publisher│ ──────────────────► │   Mosquitto Broker     │ │
 │  │  (simulator)  │                     │   (eclipse-mosquitto)  │ │
 │  └──────────────┘                      └──────────┬─────────────┘ │
 │                                                   │               │
 │  ┌──────────────┐   room/temperature              │               │
 │  │  edge_ai.py  │ ◄───────────────────────────────┤               │
 │  │  Z-score +   │   room/temperature/alerts        │               │
 │  │  threshold   │ ──────────────────────────────► │               │
 │  └──────────────┘                                 │               │
 │                                                   │               │
 │  ┌──────────────┐   Subscribes to both topics     │               │
 │  │   Node-RED   │ ◄───────────────────────────────┘               │
 │  │  Dashboard   │   http://localhost:1880/ui                       │
 │  └──────────────┘                                                  │
 └──────────────────────────────────────────────────────────────────┘

 ┌──────────────────────────────┐
 │   ESP32-S3 Hardware Node      │
 │                               │
 │  DHT22 (GPIO4)  ──► firmware  │
 │  Relay  (GPIO5) ◄── alerts   │
 │  LED green (GPIO2)            │
 │  LED red   (GPIO38) ◄── alerts│
 └──────────────────────────────┘
```

### Components

| Component | Technology | Role |
|---|---|---|
| Temperature simulator | Python / paho-mqtt | Generates HVAC sine-wave data with noise & spikes |
| Anomaly detector | Python / Z-score | Detects statistical outliers and threshold violations |
| MQTT broker | Eclipse Mosquitto 2 | Message bus for all topics |
| Dashboard | Node-RED 3 | Live gauge, chart, and alert display |
| Hardware node | ESP32-S3 + DHT22 | Physical sensor → MQTT; relay + LEDs on alert |

---

## MQTT Topics

| Topic | Direction | Payload (JSON) | Description |
|---|---|---|---|
| `room/temperature` | Publisher → Broker | `{"temperature": 23.4, "timestamp": 1700000000.0, "spike": false}` | Live temperature readings |
| `room/temperature/alerts` | EdgeAI → Broker | `{"temperature": 38.1, "timestamp": 1700000000.0, "reason": "...", "zscore": 4.2}` | Anomaly alert messages |

---

## Project Structure

```
edge-ai-groupXX/
├── docker-compose.yml          # Orchestrates all Docker services
├── python/
│   ├── Dockerfile              # Python 3.11 image for edge-ai & publisher
│   ├── mqtt_publisher.py       # Temperature simulator (sine wave + spikes)
│   └── edge_ai.py              # Z-score anomaly detector + MQTT alert publisher
├── mosquitto/
│   └── mosquitto.conf          # Mosquitto broker configuration
├── node-red/
│   └── flows.json              # Pre-built Node-RED dashboard flows
├── esp32/
│   └── src/
│       └── main.cpp            # ESP32-S3 PlatformIO firmware
└── docs/
```

---

## How to Run

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2
- (Optional for hardware) [PlatformIO](https://platformio.org/) IDE or CLI

### 1. Start the Docker stack

```bash
cd edge-ai-groupXX
docker compose up --build
```

| Service | URL / Port |
|---|---|
| Mosquitto broker | `mqtt://localhost:1883` |
| Node-RED editor | http://localhost:1880 |
| Node-RED dashboard | http://localhost:1880/ui |

The `edge-ai` container will automatically:
1. Connect to Mosquitto
2. Start the temperature simulator (`mqtt_publisher.py`) in a background thread
3. Subscribe to `room/temperature` and publish anomaly alerts to `room/temperature/alerts`

### 2. Flash the ESP32-S3 (optional hardware node)

1. Open `edge-ai-groupXX/esp32/` in PlatformIO.
2. Edit `main.cpp` – set `WIFI_SSID`, `WIFI_PASSWORD`, and `MQTT_BROKER` to the IP of your Docker host.
3. Build and upload:
   ```bash
   pio run --target upload
   ```
4. Open the serial monitor (`pio device monitor`) to observe sensor output.

### 3. Monitor with MQTT CLI (optional)

```bash
# Subscribe to all temperature topics
mosquitto_sub -h localhost -t "room/#" -v
```

---

## Anomaly Detection Logic

`edge_ai.py` uses two complementary methods:

| Method | Trigger | Description |
|---|---|---|
| Hard threshold | `temperature > 35 °C` | Immediate alert, independent of history |
| Z-score | `\|Z\| > 3.0` (window = 30) | Statistical outlier detection on a rolling window |

Both conditions publish a structured JSON alert to `room/temperature/alerts`.

---

## Results

### Simulated Data (Docker stack)

The Python simulator generates a realistic HVAC sine-wave pattern (period = 5 min, amplitude ± 3 °C around 22 °C base) with Gaussian noise (σ = 0.4 °C) and random spikes (~3% probability, +15 °C). Edge AI reliably detects both spike-type anomalies (threshold method) and subtler statistical deviations (Z-score method).

### Node-RED Dashboard

The Node-RED dashboard (http://localhost:1880/ui) displays:
- **Gauge** – current temperature with colour-coded zones (green < 30 °C, yellow 30–35 °C, red > 35 °C)
- **Line chart** – scrolling 100-sample history
- **Alert text** – latest anomaly reason and temperature value

### ESP32-S3 Hardware Node

When an anomaly alert arrives on `room/temperature/alerts`:
- The **relay (GPIO5)** activates for 5 seconds (e.g., to trigger a cooling unit)
- The **red alert LED (GPIO38)** lights up for 5 seconds
- The **green status LED (GPIO2)** blinks on each successful MQTT publish

---

## License

This project is developed as part of CO326 – Computer Networks, University of Peradeniya.
