"""
MQTT-Client für den ESP32
==========================

Verbindet zum Mosquitto-Broker, empfängt Sensor-Daten
und leitet sie an die Datenbank und Alarm-Engine weiter.

MQTT-Topics:
- serverraum/sensor/<sensor_id>: Sensor-Messwerte
- serverraum/sensor/+/status: Heartbeat/Nachricht
- serverraum/sensor/+/alarm: Alarme vom ESP32

JSON-Payload Beispiel:
{
    "sensor_id": "temp_serverraum",
    "sensor_typ": "DHT22",
    "wert": 22.5,
    "status": "OK",
    "timestamp": 1234567890
}

@author Marc-Dennis Haberland
@date 04.03.2026
Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
"""

import json
import logging
from datetime import datetime
from typing import Optional, Callable
import paho.mqtt.client as mqtt
from .config import config
from .db import datenbank

# Logger konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MqttClient:
    """
    MQTT-Client für den Empfang von Sensor-Daten
    """

    def __init__(self):
        """Initialisiert den MQTT-Client"""
        self.client = mqtt.Client(client_id=config.mqtt.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        # Callback für Alarm-Verarbeitung (wird von alarm_engine gesetzt)
        self.alarm_callback: Optional[Callable] = None

        self.verbunden = False

    def verbinden(self) -> bool:
        """
        Verbindet mit dem MQTT Broker

        @return True wenn Verbindung erfolgreich
        """
        try:
            logger.info(f"Verbinde mit MQTT Broker: {config.mqtt.broker}:{config.mqtt.port}")

            self.client.connect(
                config.mqtt.broker,
                config.mqtt.port,
                keepalive=60
            )

            # Starte MQTT-Loop im Hintergrund
            self.client.loop_start()

            return True

        except Exception as e:
            logger.error(f"MQTT Verbindungsfehler: {e}")
            return False

    def trennen(self):
        """Trennt die MQTT-Verbindung"""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT getrennt")

    def set_alarm_callback(self, callback: Callable):
        """
        Setzt Callback für Alarm-Verarbeitung

        @param callback Funktion die aufgerufen wird wenn Alarm empfangen wird
        """
        self.alarm_callback = callback

    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback wenn Verbindung hergestellt wurde
        """
        if rc == 0:
            logger.info("MQTT verbunden!")
            self.verbunden = True

            # Subscribe auf alle Sensor-Topics
            topic = f"{config.mqtt.topic_basis}/#"
            self.client.subscribe(topic, qos=config.mqtt.qos)
            logger.info(f"Subscribed auf: {topic}")

        else:
            logger.error(f"MQTT Verbindungsfehler! RC={rc}")
            self.verbunden = False

    def _on_disconnect(self, client, userdata, rc):
        """
        Callback bei Verbindungsabbruch
        """
        logger.warning(f"MQTT getrennt! RC={rc}")
        self.verbunden = False

    def _on_message(self, client, userdata, msg):
        """
        Callback wenn Nachricht empfangen wird
        Verarbeitet Sensor-Daten und leitet sie weiter
        """
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')

            logger.debug(f"MQTT Nachricht: {topic} -> {payload}")

            # Topic parsen: serverraum/sensor/<sensor_id>
            if not topic.startswith(config.mqtt.topic_basis):
                return

            # Extrahiere Sensor-ID und Topic-Typ
            teile = topic.split('/')
            if len(teile) < 3:
                return

            sensor_id = teile[2]
            nachricht_typ = teile[3] if len(teile) > 3 else "data"

            # JSON parsen
            try:
                daten = json.loads(payload)
            except json.JSONDecodeError:
                logger.error(f"JSON Fehler: {payload}")
                return

            # Verarbeite je nach Topic-Typ
            if nachricht_typ == "data" or nachricht_typ == sensor_id:
                # Normale Sensor-Daten
                self._verarbeite_sensor_daten(sensor_id, daten)

            elif nachricht_typ == "alarm":
                # Alarm vom ESP32
                self._verarbeite_alarm(sensor_id, daten)

            elif nachricht_typ == "status":
                # Heartbeat/Nachricht
                self._verarbeite_status(daten)

        except Exception as e:
            logger.error(f"Fehler bei Nachrichtenverarbeitung: {e}")

    def _verarbeite_sensor_daten(self, sensor_id: str, daten: dict):
        """
        Verarbeitet Sensor-Messdaten

        @param sensor_id Sensor-ID
        @param daten JSON-Daten
        """
        try:
            sensor_typ = daten.get('sensor_typ', 'UNBEKANNT')
            wert = float(daten.get('wert', 0))
            status = daten.get('status', 'OK')
            timestamp = daten.get('timestamp', 0)

            logger.info(f"Sensor: {sensor_id} = {wert} ({status})")

            # Sensor in Datenbank speichern (oder aktualisieren)
            datenbank.sensor_speichern(sensor_id, sensor_typ)

            # Messung speichern
            datenbank.messung_speichern(sensor_id, wert, status)

            # Alarm prüfen (wenn Callback gesetzt)
            if self.alarm_callback:
                self.alarm_callback(sensor_id, sensor_typ, wert)

        except Exception as e:
            logger.error(f"Fehler bei Sensor-Datenverarbeitung: {e}")

    def _verarbeite_alarm(self, sensor_id: str, daten: dict):
        """
        Verarbeitet Alarm-Nachricht vom ESP32

        @param sensor_id Sensor-ID
        @param daten JSON-Daten
        """
        try:
            nachricht = daten.get('nachricht', 'Alarm')
            wert = float(daten.get('wert', 0))
            alarm_typ = daten.get('sensor_typ', 'ALARM')

            logger.warning(f"ALARM von {sensor_id}: {nachricht} - Wert: {wert}")

            # Alarm in Datenbank speichern
            # alarm_typ hier vereinfacht als Typ
            datenbank.alarm_speichern(sensor_id, alarm_typ, nachricht, wert, 0)

            # Alarm-Callback aufrufen
            if self.alarm_callback:
                self.alarm_callback(sensor_id, alarm_typ, wert, ist_esp32_alarm=True)

        except Exception as e:
            logger.error(f"Fehler bei Alarmverarbeitung: {e}")

    def _verarbeite_status(self, daten: dict):
        """
        Verarbeitet Status-Nachricht (Heartbeat)

        @param daten JSON-Daten
        """
        status = daten.get('status', 'unbekannt')
        uptime = daten.get('uptime_ms', 0)
        sensor_count = daten.get('sensor_count', 0)

        logger.info(f"ESP32 Status: {status}, Uptime: {uptime}ms, Sensoren: {sensor_count}")

    def publish(self, topic: str, payload: str, qos: int = 1) -> bool:
        """
        Sendet eine MQTT-Nachricht

        @param topic Ziel-Topic
        @param payload Nachrichten-Inhalt
        @param qos QoS-Level
        @return True wenn erfolgreich
        """
        if not self.verbunden:
            logger.warning("MQTT nicht verbunden, Nachricht wird nicht gesendet")
            return False

        try:
            result = self.client.publish(topic, payload, qos)
            return result.rc == mqtt.MQTT_ERR_SUCCESS

        except Exception as e:
            logger.error(f"Fehler beim Senden: {e}")
            return False


# Globale MQTT-Instanz
mqtt_client = MqttClient()
