"""
MQTT-Simulator für lokale Tests
===============================

Dieser Simulator sendet fiktive Sensordaten an den MQTT-Broker
für lokale Tests ohne Hardware.

Verwendung:
    python simulator.py

Alle 10 Sekunden werden realistische Sensordaten gesendet:
- DS18B20 (Temperatur): 22-26°C
- SHT31 (Temperatur + Feuchtigkeit): 21-27°C / 42-58%
- MQ-2 (Rauchgas): 80-150ppm
- PIR (Bewegung): Zufällig true/false

@author Marc-Dennis Haberland
@date 17.04.2026
Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
"""

import json
import random
import time
import logging
from datetime import datetime
import paho.mqtt.client as mqtt

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MQTT Konfiguration (identisch zum Backend)
BROKER = "localhost"
PORT = 1883
TOPIC_BASE = "serverraum/sensor"

# Sensor-IDs (identisch zur Firmware)
SENSOR_DS18B20 = "ds18b20_01"
SENSOR_SHT31_TEMP = "sht31_temp_01"
SENSOR_SHT31_FEUCHTE = "sht31_feuchte_01"
SENSOR_MQ2 = "mq2_01"
SENSOR_PIR = "pir_01"


def generate_sensor_data():
    """
    Generiert realistische Sensordaten

    @return dict mit Sensor-Daten nach dem MQTT-JSON-Format
    """
    timestamp = int(datetime.now().timestamp())

    # DS18B20: Temperatur (stabil mit kleinen Schwankungen)
    ds18b20_temp = round(random.uniform(22.0, 26.0), 1)

    # SHT31: Temperatur und Feuchtigkeit
    sht31_temp = round(random.uniform(21.0, 27.0), 1)
    sht31_feuchte = round(random.uniform(42.0, 58.0), 1)

    # MQ-2: Rauchgas (normalerweise niedrig, manchmal höher)
    mq2_rauch = random.randint(80, 150)

    # PIR: Bewegung (20% Wahrscheinlichkeit)
    pir_bewegung = random.random() < 0.2

    return [
        {
            "sensor_id": SENSOR_DS18B20,
            "sensor_typ": "DS18B20",
            "wert": ds18b20_temp,
            "einheit": "°C",
            "status": "OK",
            "timestamp": timestamp
        },
        {
            "sensor_id": SENSOR_SHT31_TEMP,
            "sensor_typ": "SHT31",
            "wert": sht31_temp,
            "einheit": "°C",
            "status": "OK",
            "timestamp": timestamp
        },
        {
            "sensor_id": SENSOR_SHT31_FEUCHTE,
            "sensor_typ": "SHT31",
            "wert": sht31_feuchte,
            "einheit": "%",
            "status": "OK",
            "timestamp": timestamp
        },
        {
            "sensor_id": SENSOR_MQ2,
            "sensor_typ": "MQ2",
            "wert": mq2_rauch,
            "einheit": "ppm",
            "status": "OK",
            "timestamp": timestamp
        },
        {
            "sensor_id": SENSOR_PIR,
            "sensor_typ": "PIR",
            "wert": 1.0 if pir_bewegung else 0.0,
            "einheit": "",
            "status": "OK",
            "timestamp": timestamp
        }
    ]


def on_connect(client, userdata, flags, rc):
    """Callback wenn MQTT verbunden"""
    if rc == 0:
        logger.info("MQTT Simulator verbunden!")
    else:
        logger.error(f"MQTT Verbindungsfehler! RC={rc}")


def on_disconnect(client, userdata, rc):
    """Callback bei Verbindungsabbruch"""
    logger.warning(f"MQTT getrennt! RC={rc}")


def main():
    """Hauptschleife - sendet alle 10 Sekunden Sensordaten"""
    # MQTT Client erstellen
    client = mqtt.Client(client_id="serverraum_simulator")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    logger.info(f"Verbinde mit MQTT Broker: {BROKER}:{PORT}")

    try:
        client.connect(BROKER, PORT, keepalive=60)
        client.loop_start()
    except Exception as e:
        logger.error(f"Verbindungsfehler: {e}")
        return

    logger.info("MQTT Simulator gestartet. Sende alle 10 Sekunden Sensordaten...")
    logger.info("Strg+C zum Beenden")

    try:
        while True:
            # Sensordaten generieren
            sensoren = generate_sensor_data()

            # Jeden Sensor einzeln senden
            for daten in sensoren:
                topic = f"{TOPIC_BASE}/{daten['sensor_id']}/data"
                payload = json.dumps(daten, ensure_ascii=False)

                result = client.publish(topic, payload, qos=1)
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    logger.info(f"Gesendet: {daten['sensor_typ']} ({daten['sensor_id']}) = {daten['wert']}{daten.get('einheit', '')}")
                else:
                    logger.error(f"Sende-Fehler für {daten['sensor_id']}: RC={result.rc}")

            # 10 Sekunden warten
            time.sleep(10)

    except KeyboardInterrupt:
        logger.info("Simulator wird beendet...")
    finally:
        client.loop_stop()
        client.disconnect()
        logger.info("MQTT Simulator beendet.")


if __name__ == "__main__":
    main()
