#!/usr/bin/env python3
"""
Simuliert ESP32 Sensor-Daten via MQTT
=====================================
Publiziert alle 10 Sekunden realistische Messwerte.

Usage: python3 simulate_sensors.py
"""

import json
import random
import time
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import paho.mqtt.client as mqtt
from app.config import config

# Sensor-Konfigurationen mit realistischen Wertebereichen
SENSOREN = {
    "ds18b20_01": {"typ": "ds18b20", "einheit": "°C", "min": 18.0, "max": 28.0, "status": "OK"},
    "sht31_temp_01": {"typ": "sht31", "einheit": "°C", "min": 18.0, "max": 28.0, "status": "OK"},
    "sht31_feuchte_01": {"typ": "sht31", "einheit": "%", "min": 30.0, "max": 70.0, "status": "OK"},
    "mq2_01": {"typ": "mq2", "einheit": "ppm", "min": 50.0, "max": 180.0, "status": "OK"},
    "mq2_2": {"typ": "mq2", "einheit": "ppm", "min": 50.0, "max": 180.0, "status": "OK"},
    "mq2_6": {"typ": "mq2", "einheit": "ppm", "min": 50.0, "max": 180.0, "status": "OK"},
    "mq135_3": {"typ": "mq135", "einheit": "ppm", "min": 100.0, "max": 500.0, "status": "OK"},
    "mq135_7": {"typ": "mq135", "einheit": "ppm", "min": 100.0, "max": 500.0, "status": "OK"},
    "pir_4": {"typ": "pir", "einheit": "", "min": 0.0, "max": 1.0, "status": "OK"},
    "pir_8": {"typ": "pir", "einheit": "", "min": 0.0, "max": 1.0, "status": "OK"},
}

# Alte Wertstände für smoothing
letzte_werte = {sid: (cfg["min"] + cfg["max"]) / 2 for sid, cfg in SENSOREN.items()}


def generate_value(sensor_id: str, cfg: dict) -> float:
    """Generiert einen geglätteten Wert mit Zufallsschwankung"""
    global letzte_werte
    alter = letzte_werte[sensor_id]
    streuung = (cfg["max"] - cfg["min"]) * 0.1
    neuer = alter + random.uniform(-streuung, streuung)
    neuer = max(cfg["min"], min(cfg["max"], neuer))
    letzte_werte[sensor_id] = neuer
    return round(neuer, 1)


def main():
    client = mqtt.Client(client_id="simulator")
    client.connect(config.mqtt.broker, config.mqtt.port)
    client.loop_start()

    print(f"Simulator startet -> {config.mqtt.broker}:{config.mqtt.port}")
    print(f"Topic-Basis: {config.mqtt.topic_basis}")
    print("Drücke Ctrl+C zum Stoppen\n")

    try:
        while True:
            for sensor_id, cfg in SENSOREN.items():
                wert = generate_value(sensor_id, cfg)
                payload = {
                    "sensor_typ": cfg["typ"],
                    "wert": wert,
                    "status": cfg["status"],
                    "einheit": cfg["einheit"],
                }
                topic = f"{config.mqtt.topic_basis}/{sensor_id}/data"
                client.publish(topic, json.dumps(payload))
                print(f"  {sensor_id}: {wert}{cfg['einheit']}")

            print()
            time.sleep(10)

    except KeyboardInterrupt:
        print("\nSimulator gestoppt.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
