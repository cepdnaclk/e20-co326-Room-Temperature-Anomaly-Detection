/*
 * main.cpp – ESP32-S3 Room Temperature Anomaly Detection Node
 *
 * Hardware:
 *   DHT22 sensor   → GPIO4
 *   Relay (active-HIGH) → GPIO5
 *   Status LED (green)  → GPIO2
 *   Alert LED  (red)    → GPIO38
 *
 * Behaviour:
 *   - Reads temperature & humidity from DHT22 every 10 s
 *   - Publishes JSON to MQTT topic  room/temperature
 *   - Subscribes to  room/temperature/alerts
 *     • On alert: turns relay ON and alert LED ON for 5 s, then auto-off
 *   - Status LED blinks on every successful MQTT publish
 *
 * PlatformIO / Arduino framework for ESP32-S3.
 * Required libraries (platformio.ini):
 *   lib_deps =
 *     knolleary/PubSubClient @ ^2.8
 *     adafruit/DHT sensor library @ ^1.4.4
 *     adafruit/Adafruit Unified Sensor @ ^1.1.9
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// ── Pin definitions ────────────────────────────────────────────────────────────
#define DHT_PIN       4
#define RELAY_PIN     5
#define LED_STATUS    2
#define LED_ALERT     38

// ── DHT sensor type ────────────────────────────────────────────────────────────
#define DHT_TYPE      DHT22

// ── Wi-Fi and MQTT credentials ────────────────────────────────────────────────
// Copy esp32/src/secrets.h.example → esp32/src/secrets.h and fill in your
// values. secrets.h is listed in .gitignore and must NOT be committed.
#include "secrets.h"

// ── MQTT broker ───────────────────────────────────────────────────────────────
const uint16_t MQTT_PORT  = 1883;
const char* MQTT_CLIENT_ID = "esp32-temp-node";

// ── MQTT topics ────────────────────────────────────────────────────────────────
const char* TOPIC_PUB     = "room/temperature";
const char* TOPIC_SUB     = "room/temperature/alerts";

// ── Timing ────────────────────────────────────────────────────────────────────
const unsigned long READ_INTERVAL_MS   = 10000UL;   // 10 s between sensor reads
const unsigned long ALERT_DURATION_MS  = 5000UL;    // relay/LED on-time after alert

// ── Globals ───────────────────────────────────────────────────────────────────
DHT          dht(DHT_PIN, DHT_TYPE);
WiFiClient   wifiClient;
PubSubClient mqttClient(wifiClient);

unsigned long lastReadMs    = 0;
unsigned long alertStartMs  = 0;
bool          alertActive   = false;


// ─────────────────────────────────────────────────────────────────────────────
void connectWiFi() {
    Serial.printf("[WiFi] Connecting to %s", WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.printf("\n[WiFi] Connected – IP: %s\n",
                  WiFi.localIP().toString().c_str());
}

// ─────────────────────────────────────────────────────────────────────────────
void mqttCallback(char* topic, byte* payload, unsigned int length) {
    Serial.printf("[MQTT] Message on %s\n", topic);

    if (strcmp(topic, TOPIC_SUB) == 0) {
        Serial.println("[MQTT] ALERT received – activating relay & LED");
        digitalWrite(RELAY_PIN, HIGH);
        digitalWrite(LED_ALERT, HIGH);
        alertActive   = true;
        alertStartMs  = millis();
    }
}

// ─────────────────────────────────────────────────────────────────────────────
void connectMQTT() {
    while (!mqttClient.connected()) {
        Serial.print("[MQTT] Connecting...");
        if (mqttClient.connect(MQTT_CLIENT_ID)) {
            Serial.println(" connected");
            mqttClient.subscribe(TOPIC_SUB);
            Serial.printf("[MQTT] Subscribed to %s\n", TOPIC_SUB);
        } else {
            Serial.printf(" failed (state=%d), retrying in 5 s\n",
                          mqttClient.state());
            delay(5000);
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);

    // Configure I/O
    pinMode(RELAY_PIN,  OUTPUT);
    pinMode(LED_STATUS, OUTPUT);
    pinMode(LED_ALERT,  OUTPUT);
    digitalWrite(RELAY_PIN,  LOW);
    digitalWrite(LED_STATUS, LOW);
    digitalWrite(LED_ALERT,  LOW);

    dht.begin();

    connectWiFi();

    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setCallback(mqttCallback);

    connectMQTT();
}

// ─────────────────────────────────────────────────────────────────────────────
void loop() {
    if (!mqttClient.connected()) {
        connectMQTT();
    }
    mqttClient.loop();

    // ── Auto-deactivate alert relay/LED after ALERT_DURATION_MS ─────────────
    if (alertActive && (millis() - alertStartMs >= ALERT_DURATION_MS)) {
        digitalWrite(RELAY_PIN, LOW);
        digitalWrite(LED_ALERT,  LOW);
        alertActive = false;
        Serial.println("[Alert] Relay & LED deactivated");
    }

    // ── Periodic DHT22 read & MQTT publish ───────────────────────────────────
    if (millis() - lastReadMs >= READ_INTERVAL_MS) {
        lastReadMs = millis();

        float humidity    = dht.readHumidity();
        float temperature = dht.readTemperature();   // °C

        if (isnan(humidity) || isnan(temperature)) {
            Serial.println("[DHT22] Read failed – skipping publish");
            return;
        }

        // Build JSON payload
        StaticJsonDocument<128> doc;
        doc["temperature"] = temperature;
        doc["humidity"]    = humidity;
        doc["timestamp"]   = millis();

        char payload[128];
        serializeJson(doc, payload, sizeof(payload));

        // Publish
        if (mqttClient.publish(TOPIC_PUB, payload)) {
            Serial.printf("[MQTT] Published → %s  T=%.1f°C  H=%.1f%%\n",
                          TOPIC_PUB, temperature, humidity);
            // Blink status LED
            digitalWrite(LED_STATUS, HIGH);
            delay(100);
            digitalWrite(LED_STATUS, LOW);
        } else {
            Serial.println("[MQTT] Publish failed");
        }
    }
}
