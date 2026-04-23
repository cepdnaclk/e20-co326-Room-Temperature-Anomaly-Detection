#include <Arduino.h>

#define RELAY_PIN 4

void setup()
{
    Serial.begin(115200);
    delay(3000);
    pinMode(RELAY_PIN, OUTPUT);
    digitalWrite(RELAY_PIN, LOW); // start OFF
    Serial.println("=== Relay Test Starting ===");
    Serial.println("Watch and listen for relay clicks!");
}

void loop()
{
    // Turn relay ON
    digitalWrite(RELAY_PIN, HIGH);
    Serial.println("RELAY ON  → should hear CLICK");
    delay(2000);

    // Turn relay OFF
    digitalWrite(RELAY_PIN, LOW);
    Serial.println("RELAY OFF → should hear CLICK");
    delay(2000);
}