"""
MQTT-Client für ESP32 Sensor-Daten
===================================

Verbindet zum Mosquitto-Broker und leitet Daten an DB + AlarmEngine weiter.

Auto-Reconnect mit exponential Backoff.

@author Marc-Dennis Haberland
@date 20.04.2026
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
    """
    MQTT-Client mit Auto-Reconnect.

    Verbindet zum Mosquitto-Broker auf dem Raspberry Pi und verarbeitet
    eingehende Sensor-Daten. Implementiert exponential Backoff für Reconnects.

    Attributes:
        client:           Paho MQTT Client-Instanz
        alarm_callback:    Callback für Alarm-Verarbeitung (siehe main.py)
        ist_verbunden:     Property das Verbindungsstatus zurückgibt
    """

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
        """
        Verbindet zum konfigurierten MQTT-Broker.

        Startet den MQTT-Client-Loop in einem separaten Thread.
        Bei Verbindungsfehler wird automatisch ein Reconnect mit Backoff gestartet.

        Returns:
            True wenn Verbindung erfolgreich hergestellt wurde
        """
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
        """
        MQTT Connection Callback - wird bei erfolgreicher/trennender Verbindung aufgerufen.

        Args:
            client:     Paho Client-Instanz
            userdata:   Benutzerdefinierte Daten
            flags:      Response-Flags vom Broker
            rc:         Return-Code (0 = erfolgreich)
        """
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
        """
        MQTT Disconnect Callback - wird bei Verbindungsverlust aufgerufen.

        Bei unerwarteter Trennung (rc != 0) wird automatisch der Reconnect-Prozess
        mit exponential Backoff gestartet.

        Args:
            client:     Paho Client-Instanz
            userdata:   Benutzerdefinierte Daten
            rc:         Return-Code (0 = normal, sonst Fehler)
        """
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
        """
        Verarbeitet eingehende MQTT-Nachrichten vom ESP32-S3 Sensor.

        Erwartetes Topic-Format: {topic_basis}/{sensor_id}/{msg_typ}
        Beispiel: sensors/sensor_01/data

        Msg-Typen:
            - "data":   Sensor-Messdaten (Temperatur, Feuchtigkeit, etc.)
            - "alarm":  Alarmmeldung vom ESP32-S3
            - "status": ESP32-S3 Statusmeldung

        Args:
            client:     Paho Client-Instanz
            userdata:   Benutzerdefinierte Daten
            msg:        MQTT-Nachricht mit topic und payload
        """
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
                logger.info(f"ESP32-S3 Status: {daten.get('status')}")
            else:
                self._verarbeite_daten(sensor_id, daten)

        except Exception as e:
            logger.error(f"Message Fehler: {e}")

    def _verarbeite_daten(self, sensor_id: str, daten: dict):
        """
        Verarbeitet Sensor-Messdaten und speichert in Datenbank.

        1. Sensor in DB registrieren/aktualisieren
        2. Messwert in DB speichern
        3. Alarm-Callback aufrufen (prüft Schwellwerte)

        Args:
            sensor_id: Eindeutige Sensor-ID (z.B. "sensor_01")
            daten:    Dictionary mit:
                - sensor_typ: Typ (DS18B20, SHT31, MQ2, MQ135)
                - wert:      Messwert (float)
                - status:    Status (OK, WARN, ALARM)
                - einheit:   Einheit (°C, %, ppm)
        """
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
        """
        Verarbeitet Alarmmeldungen vom ESP32.

        Speichert den Alarm direkt in der Datenbank und löst den
        Alarm-Callback aus für zusätzliche Benachrichtigungen (Email, LED, etc.)

        Args:
            sensor_id: Eindeutige Sensor-ID
            daten:    Dictionary mit:
                - nachricht:  Alarmtext
                - wert:      gemessener Wert
                - sensor_typ: Alarmtyp
        """
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
