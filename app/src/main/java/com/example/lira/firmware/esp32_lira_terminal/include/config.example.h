#pragma once

// ==============================================================================
// LIRA ESP32 Terminal Configuration Template
// Copy to include/config.h and configure for your local environment
// ==============================================================================

// WiFi Settings
#define LIRA_WIFI_SSID "Your_Office_WiFi"
#define LIRA_WIFI_PASS "Your_Secure_Password"

// LIRA Backend API Endpoint (FastAPI)
#define LIRA_API_HOST "192.168.1.100"
#define LIRA_API_PORT 8000
#define LIRA_DEVICE_ID "ESP32-Terminal-01"
#define LIRA_DEVICE_KEY "demo-esp32-key-1042"

// Pin Definitions matching Section 10.3 of LIRA Architecture Specification
#define PIN_TFT_CS    27
#define PIN_TFT_DC    26
#define PIN_TFT_RST   25

#define PIN_RC522_SS  14
#define PIN_RC522_RST 17

#define PIN_BTN_UP    32
#define PIN_BTN_DOWN  33
#define PIN_BTN_LEFT  21
#define PIN_BTN_RIGHT 22
#define PIN_BTN_OK    4

#define PIN_BUZZER    16

// Device Behaviour Settings
#define HEARTBEAT_INTERVAL_MS 30000
#define POLL_CASES_INTERVAL_MS 10000
#define BUZZER_ENABLED true
