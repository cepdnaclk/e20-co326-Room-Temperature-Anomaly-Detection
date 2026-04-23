#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHTesp.h>
#include <ArduinoJson.h>

#define DHTPIN 4
#define RELAY_PIN 5
#define LED_GREEN 2
#define LED_RED 38

const char *SSID = "Buddhi";
const char *PASSWORD = "12345678";
const char *MQTT_SERVER = "192.168.56.1";
const int MQTT_PORT = 1883;

const char *PUB_TOPIC = "sensors/group11/temperature/data";
const char *ALERT_TOPIC = "alerts/group11/temperature/status";

DHTesp dht;
WiFiClient espClient;
PubSubClient mqttClient(espClient);

void connectWiFi()
{
    Serial.print("Connecting to WiFi");
    WiFi.begin(SSID, PASSWORD);
    int retries = 0;
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
        if (++retries > 20)
        {
            Serial.println("\nWiFi failed!");
            return;
        }
    }
    Serial.println("\nWiFi connected! IP: " + WiFi.localIP().toString());
    for (int i = 0; i < 3; i++)
    {
        digitalWrite(LED_GREEN, HIGH);
        delay(200);
        digitalWrite(LED_GREEN, LOW);
        delay(200);
    }
}

void onMqttMessage(char *topic, byte *payload, unsigned int length)
{
    String msg = "";
    for (int i = 0; i < length; i++)
        msg += (char)payload[i];
    Serial.println("Alert: " + msg);

    JsonDocument doc;
    if (deserializeJson(doc, msg))
        return;
    String status = doc["status"].as<String>();

    if (status == "ANOMALY")
    {
        digitalWrite(RELAY_PIN, HIGH);
        digitalWrite(LED_RED, HIGH);
        digitalWrite(LED_GREEN, LOW);
        Serial.println("ANOMALY — Relay ON, Red LED ON");
    }
    else
    {
        digitalWrite(RELAY_PIN, LOW);
        digitalWrite(LED_RED, LOW);
        digitalWrite(LED_GREEN, HIGH);
        Serial.println("Normal — Relay OFF, Green LED ON");
    }
}

void connectMQTT()
{
    int retries = 0;
    while (!mqttClient.connected())
    {
        Serial.print("Connecting to MQTT...");
        if (mqttClient.connect("ESP32S3_TempSensor"))
        {
            Serial.println("Connected!");
            mqttClient.subscribe(ALERT_TOPIC);
        }
        else
        {
            Serial.printf("Failed rc=%d, retry in 3s\n", mqttClient.state());
            delay(3000);
            if (++retries > 5)
            {
                Serial.println("MQTT failed!");
                return;
            }
        }
    }
}

void setup()
{
    Serial.begin(115200);
    delay(3000);
    Serial.println("\n=== Room Temp Monitor Starting ===");

    pinMode(RELAY_PIN, OUTPUT);
    pinMode(LED_GREEN, OUTPUT);
    pinMode(LED_RED, OUTPUT);
    digitalWrite(RELAY_PIN, LOW);
    digitalWrite(LED_GREEN, LOW);
    digitalWrite(LED_RED, LOW);

    dht.setup(DHTPIN, DHTesp::DHT22);
    Serial.println("DHT22 ready");

    connectWiFi();
    mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
    mqttClient.setCallback(onMqttMessage);
    connectMQTT();

    digitalWrite(LED_GREEN, HIGH);
    Serial.println("=== System Ready ===");
}

void loop()
{
    if (!mqttClient.connected())
        connectMQTT();
    mqttClient.loop();

    TempAndHumidity data = dht.getTempAndHumidity();

    if (dht.getStatus() != 0)
    {
        Serial.println("DHT22 error: " + String(dht.getStatusString()));
        delay(2000);
        return;
    }

    JsonDocument doc;
    doc["group_id"] = "group11";
    doc["temperature"] = round(data.temperature * 10.0) / 10.0;
    doc["humidity"] = round(data.humidity * 10.0) / 10.0;
    doc["timestamp"] = millis() / 1000.0;

    char buffer[200];
    serializeJson(doc, buffer);
    mqttClient.publish(PUB_TOPIC, buffer);

    Serial.printf("Sent → Temp: %.1fC  Humidity: %.1f%%\n",
                  data.temperature, data.humidity);
    delay(2000);
}
