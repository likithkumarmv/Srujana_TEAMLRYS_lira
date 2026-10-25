/*
 * ==============================================================================
 * LIRA — ESP32 Physical Case Review Terminal
 * Hardware: ESP32 DevKit V1, 2.8" ILI9341 TFT (320x240), RC522 RFID, 5 Buttons, Buzzer
 * ==============================================================================
 */

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include <TFT_eSPI.h>
#include <MFRC522.h>
#include "config.example.h"

TFT_eSPI tft = TFT_eSPI();
MFRC522 rfid(PIN_RC522_SS, PIN_RC522_RST);

struct LiraCase {
    String case_id;
    String case_ref;
    String priority;
    int risk_score;
    String status;
    String title;
    String reason_short;
    int version;
};

#define MAX_CASES 10
LiraCase caseQueue[MAX_CASES];
int totalCases = 0;
int currentCaseIndex = 0;

enum ViewMode { VIEW_QUEUE, VIEW_CASE, VIEW_VERIFY, VIEW_STATUS };
ViewMode currentView = VIEW_CASE;

unsigned long lastHeartbeat = 0;
unsigned long lastPoll = 0;
String lastTappedCardUid = "";
String lastOperatorName = "None";

void drawHeader(const char* title);
void renderCaseView();
void fetchCases();
void sendHeartbeat();
void checkRfid();
void checkButtons();

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("\n[LIRA] Starting Physical Investigation Terminal...");

    pinMode(PIN_BTN_UP, INPUT_PULLUP);
    pinMode(PIN_BTN_DOWN, INPUT_PULLUP);
    pinMode(PIN_BTN_LEFT, INPUT_PULLUP);
    pinMode(PIN_BTN_RIGHT, INPUT_PULLUP);
    pinMode(PIN_BTN_OK, INPUT_PULLUP);
    pinMode(PIN_BUZZER, OUTPUT);
    digitalWrite(PIN_BUZZER, LOW);

    // TFT Init
    tft.init();
    tft.setRotation(1); // Landscape 320x240
    tft.fillScreen(TFT_BLACK);
    tft.setTextColor(TFT_WHITE, TFT_BLACK);

    drawHeader("LIRA TERMINAL");
    tft.drawString("Connecting to WiFi...", 20, 60, 2);

    // WiFi Init
    WiFi.begin(LIRA_WIFI_SSID, LIRA_WIFI_PASS);
    int retries = 0;
    while (WiFi.status() != WL_CONNECTED && retries < 15) {
        delay(500);
        Serial.print(".");
        retries++;
    }

    // SPI for RC522
    SPI.begin(18, 19, 23, PIN_RC522_SS);
    rfid.PCD_Init();
    Serial.println("\n[LIRA] RC522 RFID Reader Ready.");

    if (WiFi.status() == WL_CONNECTED) {
        tft.drawString("WiFi Online. Fetching cases...", 20, 80, 2);
        fetchCases();
    } else {
        tft.drawString("WiFi Offline (Demo Sandbox)", 20, 80, 2);
    }

    renderCaseView();
}

void loop() {
    unsigned long now = millis();

    if (now - lastHeartbeat >= HEARTBEAT_INTERVAL_MS) {
        lastHeartbeat = now;
        sendHeartbeat();
    }

    if (now - lastPoll >= POLL_CASES_INTERVAL_MS) {
        lastPoll = now;
        fetchCases();
    }

    checkRfid();
    checkButtons();
    delay(50);
}

void drawHeader(const char* title) {
    tft.fillRect(0, 0, 320, 26, 0x1371); // #176B87 primary
    tft.setTextColor(TFT_WHITE, 0x1371);
    tft.drawString("LIRA DEFENSE", 8, 5, 2);
    tft.drawString(title, 220, 5, 2);
}

void renderCaseView() {
    tft.fillScreen(0x0842); // Dark slate
    drawHeader(currentView == VIEW_CASE ? "CASE DETAIL" : "QUEUE");

    if (totalCases == 0) {
        tft.setTextColor(TFT_WHITE, 0x0842);
        tft.drawString("No active cases in queue", 30, 80, 2);
        tft.drawString("NFC: Tap card to identify", 30, 110, 2);
        return;
    }

    LiraCase& c = caseQueue[currentCaseIndex];

    // Priority badge color
    uint16_t priorityColor = TFT_GREEN;
    if (c.priority == "critical") priorityColor = TFT_RED;
    else if (c.priority == "high") priorityColor = 0xFDE0; // Orange
    else if (c.priority == "watch") priorityColor = TFT_YELLOW;

    tft.fillRect(10, 34, 110, 22, priorityColor);
    tft.setTextColor(TFT_BLACK, priorityColor);
    tft.drawString(c.priority.toUpperCase().c_str(), 16, 38, 2);

    tft.setTextColor(TFT_WHITE, 0x0842);
    tft.drawString(c.case_ref.c_str(), 130, 38, 4);

    // Score
    tft.drawString("Risk Score:", 10, 68, 2);
    tft.setTextColor(priorityColor, 0x0842);
    tft.drawString(String(c.risk_score).c_str(), 90, 68, 4);

    tft.setTextColor(0xAD55, 0x0842);
    tft.drawString("/ 100", 140, 72, 2);

    // Title & Reason
    tft.setTextColor(TFT_WHITE, 0x0842);
    tft.drawString(c.title.substring(0, 28).c_str(), 10, 102, 2);
    tft.setTextColor(0xCE59, 0x0842);
    tft.drawString(c.reason_short.substring(0, 32).c_str(), 10, 126, 2);

    // Status bar
    tft.drawString("Status:", 10, 155, 2);
    tft.setTextColor(TFT_CYAN, 0x0842);
    tft.drawString(c.status.c_str(), 70, 155, 2);

    // Operator identification from NFC card
    tft.fillRect(0, 185, 320, 55, 0x10A2);
    tft.setTextColor(TFT_WHITE, 0x10A2);
    tft.drawString("Operator (NFC):", 10, 192, 2);
    tft.setTextColor(TFT_GREENYELLOW, 0x10A2);
    tft.drawString(lastOperatorName.c_str(), 125, 192, 2);

    tft.setTextColor(0x9CF3, 0x10A2);
    tft.drawString("[UP/DN] Move  [OK] Request Call  [TAP] Card", 10, 218, 1);
}

void checkRfid() {
    if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
        return;
    }

    String uidStr = "";
    for (byte i = 0; i < rfid.uid.size; i++) {
        if (i > 0) uidStr += ":";
        if (rfid.uid.uidByte[i] < 0x10) uidStr += "0";
        uidStr += String(rfid.uid.uidByte[i], HEX);
    }
    uidStr.toUpperCase();
    lastTappedCardUid = uidStr;

    // Beep buzzer
    if (BUZZER_ENABLED) {
        digitalWrite(PIN_BUZZER, HIGH);
        delay(60);
        digitalWrite(PIN_BUZZER, LOW);
    }

    Serial.println("[NFC] Card Tapped: " + uidStr);

    // Call API to verify card and operator association
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        String url = "http://" + String(LIRA_API_HOST) + ":" + String(LIRA_API_PORT) + "/api/v1/nfc-cards/scan";
        http.begin(url);
        http.addHeader("Content-Type", "application/json");

        JsonDocument doc;
        doc["card_uid"] = uidStr;
        doc["device_id"] = LIRA_DEVICE_ID;
        doc["action"] = "terminal_auth";
        if (totalCases > 0) doc["case_id"] = caseQueue[currentCaseIndex].case_id;

        String body;
        serializeJson(doc, body);
        int code = http.POST(body);
        if (code == 200) {
            String resp = http.getString();
            JsonDocument respDoc;
            deserializeJson(respDoc, resp);
            if (respDoc["authenticated"]) {
                lastOperatorName = respDoc["operator_name"].as<String>();
            } else {
                lastOperatorName = "UNAUTHORIZED CARD";
            }
        }
        http.end();
    } else {
        // Offline demo tag recognition
        if (uidStr == "04:A2:3B:1C") lastOperatorName = "Sarah Jenkins (Sup)";
        else if (uidStr == "04:E8:9F:4D") lastOperatorName = "Marcus Vance (Anl)";
        else lastOperatorName = "Guest Badge (" + uidStr.substring(0, 5) + ")";
    }

    renderCaseView();
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
}

void checkButtons() {
    if (digitalRead(PIN_BTN_DOWN) == LOW) {
        if (totalCases > 0) {
            currentCaseIndex = (currentCaseIndex + 1) % totalCases;
            renderCaseView();
        }
        delay(200);
    }
    if (digitalRead(PIN_BTN_UP) == LOW) {
        if (totalCases > 0) {
            currentCaseIndex = (currentCaseIndex - 1 + totalCases) % totalCases;
            renderCaseView();
        }
        delay(200);
    }
    if (digitalRead(PIN_BTN_OK) == LOW) {
        // Request verification call for current case
        if (totalCases > 0 && WiFi.status() == WL_CONNECTED) {
            tft.fillRect(20, 80, 280, 80, TFT_NAVY);
            tft.setTextColor(TFT_WHITE, TFT_NAVY);
            tft.drawString("Requesting Verification Call...", 30, 95, 2);
            tft.drawString("Connecting to Supplier...", 30, 120, 2);

            HTTPClient http;
            String url = "http://" + String(LIRA_API_HOST) + ":" + String(LIRA_API_PORT) + "/api/v1/device/cases/" + caseQueue[currentCaseIndex].case_id + "/request-verification";
            http.begin(url);
            http.addHeader("X-Device-Id", LIRA_DEVICE_ID);
            http.addHeader("X-Device-Key", LIRA_DEVICE_KEY);
            int code = http.POST("{}");
            http.end();

            delay(1200);
            fetchCases();
            renderCaseView();
        }
        delay(300);
    }
}

void fetchCases() {
    if (WiFi.status() != WL_CONNECTED) return;
    HTTPClient http;
    String url = "http://" + String(LIRA_API_HOST) + ":" + String(LIRA_API_PORT) + "/api/v1/device/cases";
    http.begin(url);
    http.addHeader("X-Device-Id", LIRA_DEVICE_ID);
    http.addHeader("X-Device-Key", LIRA_DEVICE_KEY);

    int code = http.GET();
    if (code == 200) {
        String resp = http.getString();
        JsonDocument doc;
        deserializeJson(doc, resp);
        JsonArray arr = doc.as<JsonArray>();
        totalCases = min((int)arr.size(), MAX_CASES);
        for (int i = 0; i < totalCases; i++) {
            caseQueue[i].case_id = arr[i]["case_id"].as<String>();
            caseQueue[i].case_ref = arr[i]["case_ref"].as<String>();
            caseQueue[i].priority = arr[i]["priority"].as<String>();
            caseQueue[i].risk_score = arr[i]["risk_score"].as<int>();
            caseQueue[i].status = arr[i]["status"].as<String>();
            caseQueue[i].title = arr[i]["title"].as<String>();
            caseQueue[i].reason_short = arr[i]["reason_short"].as<String>();
            caseQueue[i].version = arr[i]["version"].as<int>();
        }
    }
    http.end();
}

void sendHeartbeat() {
    if (WiFi.status() != WL_CONNECTED) return;
    HTTPClient http;
    String url = "http://" + String(LIRA_API_HOST) + ":" + String(LIRA_API_PORT) + "/api/v1/device/heartbeat";
    http.begin(url);
    http.addHeader("X-Device-Id", LIRA_DEVICE_ID);
    http.addHeader("X-Device-Key", LIRA_DEVICE_KEY);
    http.addHeader("Content-Type", "application/json");
    http.POST("{\"firmware_version\":\"1.0.4\",\"status\":\"ok\"}");
    http.end();
}
