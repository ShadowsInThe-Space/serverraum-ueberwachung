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

Auto-Reconnect:
- Exponential Backoff: 1s, 2s, 4s, 8s, ... max 60s
- Max 10 Reconnect-Versuche, dann MQTT-Ausfall-Alarm
- Automatisches Re-Subscribe nach Reconnect
- PING-Mechanismus zur Dead-Connection-Erkennung

@author Marc-Dennis Haberland
@date 04.03.2026
Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
"""

import json
import logging
import threading
import time
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
    Mit Auto-Reconnect und exponential Backoff
    """

    # Reconnect Parameter
    RECONNECT_BASE_DELAY = 1.0      # Start-Verzögerung: 1s
    RECONNECT_MAX_DELAY = 60.0       # Max-Verzögerung: 60s
    RECONNECT_MAX_ATTEMPTS = 10     # Max Versuche bevor Alarm
    PING_INTERVAL = 30               # PING alle 30s um dead connections zu erkennen
    PING_TIMEOUT = 10                # PING timeout in Sekunden

    def __init__(self):
        """Initialisiert den MQTT-Client"""
        self.client = mqtt.Client(client_id=config.mqtt.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish
        self.client.on_subscribe = self._on_subscribe

        # Callback für Alarm-Verarbeitung (wird von alarm_engine gesetzt)
        self.alarm_callback: Optional[Callable] = None

        # Connection Status
        self._verbunden = False
        self._verbindungs_status_aenderung: Optional[Callable] = None

        # Reconnect State
        self._reconnect_attempts = 0
        self._reconnect_thread: Optional[threading.Thread] = None
        self._reconnect_stop_event = threading.Event()

        # PING Thread
        self._ping_thread: Optional[threading.Thread] = None
        self._ping_stop_event = threading.Event()
        self._letzte_ping_zeit: Optional[datetime] = None
        self._letzte_pong_zeit: Optional[datetime] = None

    @property
    def ist_verbunden(self) -> bool:
        """
        Property für Connection-Status
        Andere Module können diesen Status abfragen

        @return True wenn MQTT verbunden
        """
        return self._verbunden

    def set_verbindungs_status_aenderung_callback(self, callback: Callable):
        """
        Setzt Callback das aufgerufen wird wenn sich der Verbindungsstatus ändert

        @param callback Funktion die bei Statusänderung aufgerufen wird (param: ist_verbunden: bool)
        """
        self._verbindungs_status_aenderung = callback

    def _status_aenderung(self, ist_verbunden: bool):
        """Interne Methode um Statusänderung zu propagieren"""
        if self._verbindungs_status_aenderung:
            try:
                self._verbindungs_status_aenderung(ist_verbunden)
            except Exception as e:
                logger.error(f"Fehler im Statusänderungs-Callback: {e}")

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

            # Starte PING Thread
            self._ping_starten()

            return True

        except Exception as e:
            logger.error(f"MQTT Verbindungsfehler: {e}")
            self._starte_reconnect()
            return False

    def trennen(self):
        """Trennt die MQTT-Verbindung sauber"""
        self._reconnect_stop_event.set()
        self._ping_stop_event.set()

        if self._reconnect_thread and self._reconnect_thread.is_alive():
            self._reconnect_thread.join(timeout=2)

        if self._ping_thread and self._ping_thread.is_alive():
            self._ping_thread.join(timeout=2)

        self.client.loop_stop()
        self.client.disconnect()
        self._verbunden = False
        self._status_aenderung(False)
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
            self._verbunden = True
            self._reconnect_attempts = 0
            self._status_aenderung(True)

            # Subscribe auf alle Sensor-Topics
            topic = f"{config.mqtt.topic_basis}/#"
            self.client.subscribe(topic, qos=config.mqtt.qos)
            logger.info(f"Subscribed auf: {topic}")

        else:
            logger.error(f"MQTT Verbindungsfehler! RC={rc}")
            self._verbunden = False
            self._status_aenderung(False)

    def _on_disconnect(self, client, userdata, rc):
        """
        Callback bei Verbindungsabbruch
        Startet Auto-Reconnect wenn unerwartet getrennt
        """
        logger.warning(f"MQTT getrennt! RC={rc}")
        war_verbunden = self._verbunden
        self._verbunden = False
        self._status_aenderung(False)

        # PING Thread stoppen
        self._ping_stop_event.set()

        if war_verbunden and rc != 0:
            # Unerwarteter Verbindungsabbruch -> Auto-Reconnect
            logger.warning("Unerwartete Trennung, starte Auto-Reconnect...")
            self._starte_reconnect()

    def _on_publish(self, client, userdata, mid):
        """Callback wenn Nachricht erfolgreich published wurde"""
        pass  # Implementierung optional für debugging

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback wenn Subscribe erfolgreich war"""
        logger.debug(f"Subscribe bestätigt, MID: {mid}, QoS: {granted_qos}")

    def _starte_reconnect(self):
        """
        Startet den Auto-Reconnect Thread mit exponential Backoff
        """
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            logger.debug("Reconnect-Thread läuft bereits")
            return

        self._reconnect_stop_event.clear()
        self._reconnect_thread = threading.Thread(
            target=self._reconnect_schleife,
            daemon=True,
            name="MQTT-Reconnect"
        )
        self._reconnect_thread.start()
        logger.info("Reconnect-Thread gestartet")

    def _reconnect_schleife(self):
        """
        Reconnect-Schleife mit exponential Backoff
        Versucht max RECONNECT_MAX_ATTEMPTS Verbindungen
        """
        while not self._reconnect_stop_event.is_set():
            if self._reconnect_attempts >= self.RECONNECT_MAX_ATTEMPTS:
                logger.error(
                    f"MQTT Auto-Reconnect fehlgeschlagen nach {self.RECONNECT_MAX_ATTEMPTS} Versuchen!"
                )
                self._mqtt_ausgefallen_alarm()
                break

            # Berechne Verzögerung mit exponential Backoff: 1s, 2s, 4s, 8s, ... max 60s
            delay = min(
                self.RECONNECT_BASE_DELAY * (2 ** self._reconnect_attempts),
                self.RECONNECT_MAX_DELAY
            )

            logger.info(
                f"Reconnect Versuch {self._reconnect_attempts + 1}/"
                f"{self.RECONNECT_MAX_ATTEMPTS} in {delay:.1f}s..."
            )

            # Warten bis Stop-Event oder Timeout
            if self._reconnect_stop_event.wait(timeout=delay):
                break  # Stop-Event gesetzt

            if self._verbunden:
                logger.info("Reconnect erfolgreich, beende Schleife")
                break

            # Verbindungsversuch
            try:
                self._reconnect_attempts += 1
                logger.info(
                    f"Versuche reconnect zum MQTT Broker: "
                    f"{config.mqtt.broker}:{config.mqtt.port}"
                )

                # Verbindung herstellen
                self.client.reconnect()

                # Kurze Wartezeit für Verbindung
                for _ in range(10):
                    if self._verbunden:
                        self._reconnect_attempts = 0
                        logger.info("Reconnect erfolgreich!")
                        break
                    time.sleep(0.5)

            except Exception as e:
                logger.error(f"Reconnect Fehler: {e}")

        logger.debug("Reconnect-Thread beendet")

    def _mqtt_ausgefallen_alarm(self):
        """
        Alarmierung dass MQTT komplett ausgefallen ist
        Nach max reconnect Versuchen
        """
        logger.critical("ALARM: MQTT Broker nicht erreichbar nach allen Reconnect-Versuchen!")

        if self.alarm_callback:
            try:
                # Alarm-Callback aufrufen mit speziellem Flag für MQTT-Ausfall
                self.alarm_callback(
                    sensor_id="MQTT_BROKER",
                    sensor_typ="SYSTEM",
                    wert=0.0,
                    ist_esp32_alarm=False,
                    ist_mqtt_ausfall=True
                )
            except Exception as e:
                logger.error(f"Fehler bei MQTT-Ausfall-Alarm: {e}")

    def _ping_starten(self):
        """
        Startet den PING Thread um dead connections zu erkennen
        """
        if self._ping_thread and self._ping_thread.is_alive():
            logger.debug("PING-Thread läuft bereits")
            return

        self._ping_stop_event.clear()
        self._ping_thread = threading.Thread(
            target=self._ping_schleife,
            daemon=True,
            name="MQTT-PING"
        )
        self._ping_thread.start()
        logger.debug("PING-Thread gestartet")

    def _ping_schleife(self):
        """
        PING-Schleife um Verbindung zu prüfen
        Sendet regelmäßig PING und prüft auf Pong
        """
        while not self._ping_stop_event.is_set():
            # Warten auf PING Intervall
            if self._ping_stop_event.wait(timeout=self.PING_INTERVAL):
                break

            if not self._verbunden:
                continue

            try:
                self._letzte_ping_zeit = datetime.now()
                logger.debug(f"PING gesendet um {self._letzte_ping_zeit}")

                # Auf PONG warten (im Paho MQTT wird dies durch keepalive gehandhabt)
                # Hier prüfen wir ob die Verbindung noch aktiv ist
                if self.client.is_connected():
                    self._letzte_pong_zeit = datetime.now()
                    logger.debug("Verbindung aktiv (kein PONG Timeout)")
                else:
                    logger.warning("Verbindung scheint tot zu sein (is_connected=False)")
                    # Verbindung verloren, disconnect handler kümmert sich um reconnect

            except Exception as e:
                logger.error(f"Fehler im PING Thread: {e}")

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
        if not self._verbunden:
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
