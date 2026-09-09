/**
 * @file Folie10_WLANReconnect.cpp
 * Non-Blocking WLAN-Reconnect mit Event-Handler
 */

// Non-Blocking Variablen
bool wlanVerbunden = false;
bool mqttVerbunden = false;
unsigned long letzterWlanReconnect = 0;

void onWiFiEvent(WiFiEvent_t event, WiFiEventInfo_t info) {
    switch (event) {
        case ARDUINO_EVENT_WIFI_STA_GOT_IP:
            wlanVerbunden = true;
            Serial.printf("[WLAN] IP: %s\n", WiFi.localIP().toString().c_str());
            break;
        case ARDUINO_EVENT_WIFI_STA_DISCONNECTED:
            wlanVerbunden = false;
            Serial.println("[WLAN] Getrennt!");
            break;
    }
}

void verbindeWLANNichtBlockierend() {
    if (wlanVerbunden) return;
    if (millis() - letzterWlanReconnect < 5000) return;

    Serial.printf("[WLAN] Verbinde mit %s...\n", WIFI_SSID);
    WiFi.onEvent(onWiFiEvent);  // Event-Handler registrieren
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    letzterWlanReconnect = millis();
}

void loop() {
    // Non-blocking - Loop wird NICHT blockiert!
    verbindeWLANNichtBlockierend();

    if (mqttVerbunden) {
        mqttClient.loop();
    }
    // ... andere Aufgaben laufen weiter!
}
