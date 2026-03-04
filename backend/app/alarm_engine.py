"""
Alarm-Engine für Serverraum-Überwachung
=======================================

Prüft Schwellwerte und löst Alarmierung aus:
- E-Mail Benachrichtigung
- Warn-LED (GPIO am Raspberry Pi)
- Buzzer (akustischer Alarm)
- Dashboard-Benachrichtigung

Jeder Alarm wird in der Datenbank protokolliert.

@author Marc-Dennis Haberland
@date 04.03.2026
Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
"""

import logging
import smtplib
import RPi.GPIO as GPIO
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from .config import config
from .db import datenbank

# Logger konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlarmEngine:
    """
    Alarm-Engine für automatische Überwachung und Alarmierung
    """

    def __init__(self):
        """Initialisiert die Alarm-Engine"""
        # GPIO für LED und Buzzer initialisieren
        self._gpio_initialisiert = False

        # Letzten Alarm speichern um Spam zu vermeiden
        self.letzter_alarm_zeit = {}
        self.alarm_abstand_sekunden = 60  # Mindestens 60 Sekunden zwischen Alarmen

    def initialisiere_gpio(self):
        """
        Initialisiert die GPIO-Pins für LED und Buzzer

        @note Raspberry Pi spezifisch - wird auf anderen Systemen ignoriert
        """
        if self._gpio_initialisiert:
            return

        try:
            # Verwende BCM-Nummerierung (nicht physikalische Pins!)
            GPIO.setmode(GPIO.BCM)

            # LED Pin als Ausgang
            if config.alarm.led_enabled:
                GPIO.setup(config.alarm.led_pin, GPIO.OUT)
                GPIO.output(config.alarm.led_pin, GPIO.LOW)
                logger.info(f"LED konfiguriert: GPIO {config.alarm.led_pin}")

            # Buzzer Pin als Ausgang
            if config.alarm.buzzer_enabled:
                GPIO.setup(config.alarm.buzzer_pin, GPIO.OUT)
                GPIO.output(config.alarm.buzzer_pin, GPIO.LOW)
                logger.info(f"Buzzer konfiguriert: GPIO {config.alarm.buzzer_pin}")

            self._gpio_initialisiert = True

        except Exception as e:
            logger.warning(f"GPIO Initialisierung fehlgeschlagen: {e}")
            # GPIO nicht verfügbar (kein Raspberry Pi oder keine Rechte)

    def pruefe_alarm(self, sensor_id: str, sensor_typ: str, wert: float) -> Optional[dict]:
        """
        Prüft einen Messwert gegen Schwellwerte

        @param sensor_id Sensor-ID
        @param sensor_typ Sensor-Typ (DHT22, MQ2, etc.)
        @param wert Aktueller Messwert
        @return Alarm-Dictionary wenn Alarm ausgelöst, sonst None
        """
        alarm = None

        # Prüfe Schwellwerte je nach Sensor-Typ
        if sensor_typ in ["DHT22", "DS18B20"]:
            # Temperatur prüfen
            if wert > config.alarm.temperatur_max:
                alarm = {
                    'sensor_id': sensor_id,
                    'alarm_typ': 'TEMPERATUR_HOCH',
                    'nachricht': f'Temperatur zu hoch: {wert:.1f}°C (Max: {config.alarm.temperatur_max}°C)',
                    'wert': wert,
                    'schwellwert': config.alarm.temperatur_max
                }
            elif wert < config.alarm.temperatur_min:
                alarm = {
                    'sensor_id': sensor_id,
                    'alarm_typ': 'TEMPERATUR_NIEDRIG',
                    'nachricht': f'Temperatur zu niedrig: {wert:.1f}°C (Min: {config.alarm.temperatur_min}°C)',
                    'wert': wert,
                    'schwellwert': config.alarm.temperatur_min
                }

        elif sensor_typ == "MQ2":
            # Rauchgas prüfen
            if wert > config.alarm.rauchgas_max:
                alarm = {
                    'sensor_id': sensor_id,
                    'alarm_typ': 'RAUCHGAS',
                    'nachricht': f'Rauchgas überschritten: {wert:.0f} ppm (Max: {config.alarm.rauchgas_max} ppm)',
                    'wert': wert,
                    'schwellwert': config.alarm.rauchgas_max
                }

        elif sensor_typ == "MQ135":
            # Luftqualität prüfen
            if wert > config.alarm.luftqualitaet_max:
                alarm = {
                    'sensor_id': sensor_id,
                    'alarm_typ': 'LUFTQUALITAET',
                    'nachricht': f'Luftqualität schlecht: {wert:.0f} ppm (Max: {config.alarm.luftqualitaet_max} ppm)',
                    'wert': wert,
                    'schwellwert': config.alarm.luftqualitaet_max
                }

        # Wenn Alarm ausgelöst wurde
        if alarm:
            # Prüfe ob nicht zu schnell alarmiert werden soll (Spam-Schutz)
            alarm_key = f"{sensor_id}_{alarm['alarm_typ']}"
            import time
            jetzige_zeit = time.time()

            if alarm_key in self.letzter_alarm_zeit:
                zeit_seit_letztem_alarm = jetzige_zeit - self.letzter_alarm_zeit[alarm_key]
                if zeit_seit_letztem_alarm < self.alarm_abstand_sekunden:
                    logger.debug(f"Alarm unterdrückt (Spam-Schutz): {alarm_key}")
                    return None

            # Alarm-Zeit speichern
            self.letzter_alarm_zeit[alarm_key] = jetzige_zeit

        return alarm

    def alarm_ausloesen(self, alarm: dict):
        """
        Löst die Alarmierung aus

        @param alarm Alarm-Dictionary mit Details
        """
        sensor_id = alarm['sensor_id']
        alarm_typ = alarm['alarm_typ']
        nachricht = alarm['nachricht']

        logger.warning(f"ALARM: {nachricht}")

        # 1. Alarm in Datenbank speichern
        alarm_id = datenbank.alarm_speichern(
            sensor_id=sensor_id,
            alarm_typ=alarm_typ,
            nachricht=nachricht,
            wert=alarm['wert'],
            schwellwert=alarm['schwellwert']
        )

        # 2. Verschiedene Alarmierungsmethoden aufrufen
        if config.alarm.email_enabled:
            self._sende_email(alarm)

        if config.alarm.buzzer_enabled:
            self._aktiviere_buzzer()

        if config.alarm.led_enabled:
            self._aktiviere_led()

    def _sende_email(self, alarm: dict):
        """
        Sendet E-Mail Benachrichtigung

        @param alarm Alarm-Details
        """
        if not config.alarm.email_enabled:
            return

        try:
            # E-Mail Nachricht erstellen
            nachricht = MIMEMultipart("alternative")
            nachricht["Subject"] = f"⚠️ Serverraum Alarm: {alarm['alarm_typ']}"
            nachricht["From"] = config.alarm.email_absender
            nachricht["To"] = config.alarm.email_empfaenger

            # Text-Körper
            text = f"""
Serverraum-Überwachung - ALARM

{alarm['nachricht']}

Sensor: {alarm['sensor_id']}
Wert: {alarm['wert']}
Schwellwert: {alarm['schwellwert']}
Zeitpunkt: jetzt

Diese E-Mail wurde automatisch vom Überwachungssystem gesendet.
"""

            # HTML-Körper (für bessere Darstellung)
            html = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: red;">⚠️ Serverraum Alarm</h2>
    <p><strong>{alarm['nachricht']}</strong></p>
    <table>
        <tr><td><strong>Sensor:</strong></td><td>{alarm['sensor_id']}</td></tr>
        <tr><td><strong>Wert:</strong></td><td>{alarm['wert']}</td></tr>
        <tr><td><strong>Schwellwert:</strong></td><td>{alarm['schwellwert']}</td></tr>
    </table>
    <hr>
    <p style="color: gray; font-size: small;">
        Diese E-Mail wurde automatisch vom Serverraum-Überwachungssystem gesendet.
    </p>
</body>
</html>
"""

            # Beide Versionen anhängen
            nachricht.attach(MIMEText(text, "plain"))
            nachricht.attach(MIMEText(html, "html"))

            # SMTP-Verbindung herstellen und senden
            with smtplib.SMTP(config.alarm.email_smtp_server, config.alarm.email_smtp_port) as server:
                server.starttls()  # TLS-Verschlüsselung
                server.login(config.alarm.email_absender, config.alarm.email_passwort)
                server.sendmail(
                    config.alarm.email_absender,
                    config.alarm.email_empfaenger,
                    nachricht.as_string()
                )

            logger.info(f"E-Mail Alarm gesendet an {config.alarm.email_empfaenger}")

        except Exception as e:
            logger.error(f"E-Mail Versand fehlgeschlagen: {e}")

    def _aktiviere_led(self):
        """
        Aktiviert die Warn-LED

        @note Raspberry Pi spezifisch
        """
        if not config.alarm.led_enabled or not self._gpio_initialisiert:
            return

        try:
            # LED an
            GPIO.output(config.alarm.led_pin, GPIO.HIGH)
            logger.info("Warn-LED aktiviert")

            # LED nach 5 Sekunden wieder aus
            import threading
            threading.Timer(5.0, lambda: GPIO.output(config.alarm.led_pin, GPIO.LOW)).start()

        except Exception as e:
            logger.error(f"LED Fehler: {e}")

    def _aktiviere_buzzer(self):
        """
        Aktiviert den Buzzer (akustischer Alarm)

        @note Raspberry Pi spezifisch
        """
        if not config.alarm.buzzer_enabled or not self._gpio_initialisiert:
            return

        try:
            # Buzzer an
            GPIO.output(config.alarm.buzzer_pin, GPIO.HIGH)
            logger.info("Buzzer aktiviert")

            # Buzzer nach 2 Sekunden wieder aus
            import threading
            threading.Timer(2.0, lambda: GPIO.output(config.alarm.buzzer_pin, GPIO.LOW)).start()

        except Exception as e:
            logger.error(f"Buzzer Fehler: {e}")

    def cleanup(self):
        """
        Räumt GPIO-Pins auf beim Beenden

        @note Raspberry Pi spezifisch
        """
        if self._gpio_initialisiert:
            try:
                GPIO.cleanup()
                logger.info("GPIO aufgeräumt")
            except Exception as e:
                logger.error(f"GPIO Cleanup Fehler: {e}")


# Globale Alarm-Instanz
alarm_engine = AlarmEngine()
