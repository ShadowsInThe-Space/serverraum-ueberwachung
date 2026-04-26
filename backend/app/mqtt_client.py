"""
MQTT-Client für ESP32 Sensor-Daten
===================================

Verbindet zum Mosquitto-Broker und leitet Daten an DB + AlarmEngine weiter.

Auto-Reconnect mit exponential Backoff.

@author Marc-Dennis Haberland
@date 04.03.2026
"""

import json
import logging
import threading
import time
from typing import Optional, Callable

import paho.mqtt.client as mqtt

from .config import config
from .db import datenbank

logger = logging.getLogger(__name__)


class MqttClient:
    """MQTT-Client mit Auto-Reconnect"""

    MAX_RETRIES = 10

    def __init__(self):
        self.client = mqtt.Client(client_id=config.mqtt.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        self._verbunden = False
        self.alarm_callback: Optional[Callable] = None

        self._reconnect_thread: Optional[threading.Thread] = None
        self._reconnect_stop = threading.Event()
        self._retry_count = 0

    @property
    def ist_verbunden(self) -> bool:
        return self._verbunden

    def verbinden(self) -> bool:
        """Verbindet zum Broker"""
        try:
            logger.info(f"Verbinde zu {config.mqtt.broker}:{config.mqtt.port}")
            self.client.connect(config.mqtt.broker, config.mqtt.port, keepalive=60)
            self.client.loop_start()
            return True
        except Exception as e:
            logger.error(f"Verbindungsfehler: {e}")
            self._starte_reconnect()
            return False

    def trennen(self):
        """Trennt Verbindung"""
        self._reconnect_stop.set()
        self.client.loop_stop()
        self.client.disconnect()
        self._verbunden = False

    def set_alarm_callback(self, callback: Callable):
        self.alarm_callback = callback

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._verbunden = True
            self._retry_count = 0
            self._reconnect_stop.set()
            topic = f"{config.mqtt.topic_basis}/#"
            self.client.subscribe(topic, qos=config.mqtt.qos)
            logger.info(f"MQTT verbunden, subscribed auf {topic}")
        else:
            logger.error(f"MQTT RC={rc}")

    def _on_disconnect(self, client, userdata, rc):
        self._verbunden = False
        if rc != 0:
            logger.warning(f"MQTT getrennt (RC={rc}), starte Reconnect...")
            self._starte_reconnect()

    def _starte_reconnect(self):
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            return
        self._reconnect_stop.clear()
        self._reconnect_thread = threading.Thread(target=self._reconnect, daemon=True)
        self._reconnect_thread.start()

    def _reconnect(self):
        """Exponential Backoff Reconnect"""
        while not self._reconnect_stop.is_set():
            if self._retry_count >= self.MAX_RETRIES:
                logger.critical("MQTT: Max retries erreicht")
                break

            delay = min(1.0 * (2**self._retry_count), 60.0)
            logger.info(f"Reconnect in {delay:.1f}s (Versuch {self._retry_count + 1})")

            if self._reconnect_stop.wait(timeout=delay):
                break

            try:
                self._retry_count += 1
                self.client.reconnect()
                for _ in range(10):
                    if self._verbunden:
                        self._retry_count = 0
                        break
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"Reconnect Fehler: {e}")

    def _on_message(self, client, userdata, msg):
        """Verarbeitet eingehende MQTT-Nachrichten"""
        try:
            topic = msg.topic
            if not topic.startswith(config.mqtt.topic_basis):
                return

            teile = topic.split("/")
            if len(teile) < 3:
                return

            sensor_id = teile[2]
            msg_typ = teile[3] if len(teile) > 3 else "data"

            try:
                daten = json.loads(msg.payload.decode("utf-8"))
            except json.JSONDecodeError:
                logger.error(f"JSON Fehler: {msg.payload}")
                return

            # Routing
            if msg_typ == "alarm":
                self._verarbeite_alarm(sensor_id, daten)
            elif msg_typ == "status":
                logger.info(f"ESP32 Status: {daten.get('status')}")
            else:
                self._verarbeite_daten(sensor_id, daten)

        except Exception as e:
            logger.error(f"Message Fehler: {e}")

    def _verarbeite_daten(self, sensor_id: str, daten: dict):
        """Sensor-Daten verarbeiten"""
        try:
            sensor_typ = daten.get("sensor_typ", "UNBEKANNT")
            wert = float(daten.get("wert", 0))
            status = daten.get("status", "OK")
            einheit = daten.get("einheit")

            datenbank.sensor_speichern(sensor_id, sensor_typ)
            datenbank.messung_speichern(sensor_id, wert, status, einheit)

            if self.alarm_callback:
                self.alarm_callback(sensor_id, sensor_typ, wert)

        except Exception as e:
            logger.error(f"Datenverarbeitung Fehler: {e}")

    def _verarbeite_alarm(self, sensor_id: str, daten: dict):
        """Alarm vom ESP32 verarbeiten"""
        try:
            nachricht = daten.get("nachricht", "Alarm")
            wert = float(daten.get("wert", 0))
            alarm_typ = daten.get("sensor_typ", "ALARM")

            datenbank.alarm_speichern(sensor_id, alarm_typ, nachricht, wert, 0)

            if self.alarm_callback:
                self.alarm_callback(sensor_id, alarm_typ, wert)

        except Exception as e:
            logger.error(f"Alarmverarbeitung Fehler: {e}")


mqtt_client = MqttClient()
