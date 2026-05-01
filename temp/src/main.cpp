#include <Arduino.h>
#include <USB.h>
#include <USBCDC.h>

USBCDC USBSerial;

#define RELAY_PIN  5
#define LED_GREEN  2
#define LED_RED    38

// ── 4 Scenarios ───────────────────────────────────────
struct Scenario {
    const char* name;
    float temp;
    float humidity;
    const char* description;
    int duration;   // seconds to hold this state
};

Scenario scenarios[] = {
    // name,          temp,  hum,   description,                    duration
    {"NORMAL - Morning", 22.5,  55.0, "Comfortable room temperature",  10},
    {"NORMAL - Afternoon",27.3, 62.0, "Slightly warm but acceptable",  10},
    {"SUPER HOT",        42.0,  80.0, "OVERHEATING! AC failure!",      10},
    {"SUPER COOL",       10.5,  30.0, "TOO COLD! Heating failure!",    10},
};

int totalScenarios = 4;
int currentScenario = 0;

// Thresholds
#define TEMP_HIGH  35.0    // above this = too hot
#define TEMP_LOW   15.0    // below this = too cold

// ──────────────────────────────────────────────────────

void printDivider() {
    USBSerial.println("========================================");
}

void setNormal(Scenario s) {
    digitalWrite(LED_GREEN, HIGH);
    digitalWrite(LED_RED,   LOW);
    digitalWrite(RELAY_PIN, LOW);
    USBSerial.println("STATUS  : ✅ NORMAL");
    USBSerial.println("LED     : GREEN ON");
    USBSerial.println("BUZZER  : OFF");
}

void setAnomaly(Scenario s) {
    digitalWrite(LED_GREEN, LOW);
    digitalWrite(LED_RED,   HIGH);
    digitalWrite(RELAY_PIN, HIGH);
    USBSerial.println("STATUS  : 🚨 ANOMALY DETECTED");
    USBSerial.println("LED     : RED ON");
    USBSerial.println("BUZZER  : ON");
}

void runScenario(Scenario s) {
    printDivider();
    USBSerial.printf("SCENARIO : %s\n",   s.name);
    USBSerial.printf("TEMP     : %.1fC\n", s.temp);
    USBSerial.printf("HUMIDITY : %.1f%%\n", s.humidity);
    USBSerial.printf("DESC     : %s\n",   s.description);
    USBSerial.println("----------------------------------------");

    if (s.temp > TEMP_HIGH) {
        setAnomaly(s);
        USBSerial.println("REASON  : Temperature too HIGH!");
    } else if (s.temp < TEMP_LOW) {
        setAnomaly(s);
        USBSerial.println("REASON  : Temperature too LOW!");
    } else {
        setNormal(s);
        USBSerial.println("REASON  : Within safe range");
    }

    USBSerial.printf("HOLD FOR : %d seconds\n", s.duration);
    printDivider();

    // count down so you know when next scenario starts
    for (int i = s.duration; i > 0; i--) {
        //USBSerial.printf("  Next scenario in %d seconds...\n", i);
        delay(1000);
    }
}

void setup() {
    USB.begin();
    USBSerial.begin(115200);
    delay(3000);

    pinMode(RELAY_PIN, OUTPUT);
    pinMode(LED_GREEN, OUTPUT);
    pinMode(LED_RED,   OUTPUT);

    digitalWrite(RELAY_PIN, LOW);
    digitalWrite(LED_GREEN, LOW);
    digitalWrite(LED_RED,   LOW);

    printDivider();
    USBSerial.println("  ROOM TEMPERATURE ANOMALY DETECTOR");
    USBSerial.println("  4 Scenario Physical Test");
    USBSerial.printf("  Hot threshold  : > %.1fC\n", TEMP_HIGH);
    USBSerial.printf("  Cold threshold : < %.1fC\n", TEMP_LOW);
    printDivider();
    delay(3000);
}

void loop() {
    Scenario s = scenarios[currentScenario];
    runScenario(s);

    currentScenario++;
    if (currentScenario >= totalScenarios) {
        currentScenario = 0;
        USBSerial.println("\n>>> All 4 scenarios complete - restarting cycle <<<\n");
        delay(3000);
    }
}