"""
Alarm-Engine für Serverraum-Überwachung
=======================================

Implementiert das Observer/Notifier-Pattern für Alarmierung:
- E-Mail Benachrichtigung (mit Retry-Logic)
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
import time
import threading
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List

try:
    import RPi.GPIO as GPIO
    GPIO_VERFUEGBAR = True
except ImportError:
    GPIO_VERFUEGBAR = False

from .config import config
from .db import datenbank

# Logger konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlarmNotifier(ABC):
    """
    Abstrakte Basisklasse für alle Alarm-Notifier.
    Implementiert das Observer-Pattern.
    """

    @abstractmethod
    def senden(self, alarm: dict) -> bool:
        """
        Sendet die Alarmmeldung über diesen Kanal.

        @param alarm Alarm-Dictionary mit Details
        @return True wenn erfolgreich, False sonst
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Gibt den Namen des Notifiers zurück."""
        pass


class EmailNotifier(AlarmNotifier):
    """
    E-Mail Notifier mit Retry-Logic.
    Versucht max. 3 Mal den Versand bei Fehlern.
    """

    MAX_RETRIES = 3
    RETRY_VERZOEGERUNG = 2  # Sekunden zwischen Retry-Versuchen

    def __init__(self):
        self._name = "E-Mail"

    @property
    def name(self) -> str:
        return self._name

    def senden(self, alarm: dict) -> bool:
        """
        Sendet E-Mail mit Retry-Logic.

        @param alarm Alarm-Details
        @return True wenn erfolgreich, False sonst
        """
        if not config.alarm.email_enabled:
            return True  # Nichts zu tun ist kein Fehler

        for versuch in range(1, self.MAX_RETRIES + 1):
            try:
                self._sende_email(alarm)
                logger.info(f"E-Mail Alarm gesendet an {config.alarm.email_empfaenger}")
                return True

            except Exception as e:
                logger.warning(
                    f"E-Mail Versand fehlgeschlagen (Versuch {versuch}/{self.MAX_RETRIES}): {e}"
                )

                if versuch < self.MAX_RETRIES:
                    time.sleep(self.RETRY_VERZOEGERUNG)

        logger.error(f"E-Mail Alarm nach {self.MAX_RETRIES} Versuchen fehlgeschlagen")
        return False

    def _sende_email(self, alarm: dict):
        """Interne Methode für eigentlichen E-Mail-Versand."""
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


class GPIOLedNotifier(AlarmNotifier):
    """
    LED-Notifier für Raspberry Pi GPIO.
    Schaltet LED für 5 Sekunden ein.
    """

    def __init__(self):
        self._name = "LED"
        self._gpio_initialisiert = False

    @property
    def name(self) -> str:
        return self._name

    def initialisiere(self):
        """Initialisiert GPIO-Pin für LED."""
        if self._gpio_initialisiert or not GPIO_VERFUEGBAR:
            return

        if not config.alarm.led_enabled:
            return

        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(config.alarm.led_pin, GPIO.OUT)
            GPIO.output(config.alarm.led_pin, GPIO.LOW)
            self._gpio_initialisiert = True
            logger.info(f"LED konfiguriert: GPIO {config.alarm.led_pin}")
        except Exception as e:
            logger.warning(f"LED GPIO Initialisierung fehlgeschlagen: {e}")

    def senden(self, alarm: dict) -> bool:
        """
        Aktiviert die Warn-LED für 5 Sekunden.

        @param alarm Alarm-Details (werden ignoriert)
        @return True wenn erfolgreich, False sonst
        """
        if not config.alarm.led_enabled or not self._gpio_initialisiert:
            return True

        try:
            GPIO.output(config.alarm.led_pin, GPIO.HIGH)
            logger.info("Warn-LED aktiviert")

            # LED nach 5 Sekunden wieder aus
            threading.Timer(5.0, lambda: self._led_ausschalten()).start()
            return True

        except Exception as e:
            logger.error(f"LED Fehler: {e}")
            return False

    def _led_ausschalten(self):
        """Schaltet LED aus (Thread-sicher)."""
        try:
            if self._gpio_initialisiert:
                GPIO.output(config.alarm.led_pin, GPIO.LOW)
        except Exception:
            pass


class GPIOBuzzerNotifier(AlarmNotifier):
    """
    Buzzer-Notifier für Raspberry Pi GPIO.
    Schaltet Buzzer für 2 Sekunden ein.
    """

    def __init__(self):
        self._name = "Buzzer"
        self._gpio_initialisiert = False

    @property
    def name(self) -> str:
        return self._name

    def initialisiere(self):
        """Initialisiert GPIO-Pin für Buzzer."""
        if self._gpio_initialisiert or not GPIO_VERFUEGBAR:
            return

        if not config.alarm.buzzer_enabled:
            return

        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(config.alarm.buzzer_pin, GPIO.OUT)
            GPIO.output(config.alarm.buzzer_pin, GPIO.LOW)
            self._gpio_initialisiert = True
            logger.info(f"Buzzer konfiguriert: GPIO {config.alarm.buzzer_pin}")
        except Exception as e:
            logger.warning(f"Buzzer GPIO Initialisierung fehlgeschlagen: {e}")

    def senden(self, alarm: dict) -> bool:
        """
        Aktiviert den Buzzer für 2 Sekunden.

        @param alarm Alarm-Details (werden ignoriert)
        @return True wenn erfolgreich, False sonst
        """
        if not config.alarm.buzzer_enabled or not self._gpio_initialisiert:
            return True

        try:
            GPIO.output(config.alarm.buzzer_pin, GPIO.HIGH)
            logger.info("Buzzer aktiviert")

            # Buzzer nach 2 Sekunden wieder aus
            threading.Timer(2.0, lambda: self._buzzer_ausschalten()).start()
            return True

        except Exception as e:
            logger.error(f"Buzzer Fehler: {e}")
            return False

    def _buzzer_ausschalten(self):
        """Schaltet Buzzer aus (Thread-sicher)."""
        try:
            if self._gpio_initialisiert:
                GPIO.output(config.alarm.buzzer_pin, GPIO.LOW)
        except Exception:
            pass


class DashboardNotifier(AlarmNotifier):
    """
    Dashboard-Notifier.
    Protokolliert Alarm für Web-Dashboard-Anzeige.
    """

    def __init__(self):
        self._name = "Dashboard"
        self._aktive_alarme = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def aktive_alarme(self) -> List[dict]:
        """Gibt Liste der aktiven Alarme zurück für Dashboard."""
        return self._aktive_alarme.copy()

    def senden(self, alarm: dict) -> bool:
        """
        Fügt Alarm zur aktiven Alarm-Liste hinzu.

        @param alarm Alarm-Details
        @return True (immer erfolgreich)
        """
        try:
            alarm_entry = {
                'sensor_id': alarm['sensor_id'],
                'alarm_typ': alarm['alarm_typ'],
                'nachricht': alarm['nachricht'],
                'wert': alarm['wert'],
                'schwellwert': alarm['schwellwert'],
                'zeitstempel': time.time()
            }
            self._aktive_alarme.append(alarm_entry)

            # Alte Alarme nach 10 Minuten entfernen
            self._bereinige_alte_alarme()

            logger.info(f"Dashboard-Notifier: Alarm erfasst")
            return True

        except Exception as e:
            logger.error(f"Dashboard-Notifier Fehler: {e}")
            return False

    def _bereinige_alte_alarme(self):
        """Entfernt Alarme älter als 10 Minuten."""
        aktuelle_zeit = time.time()
        self._aktive_alarme = [
            a for a in self._aktive_alarme
            if aktuelle_zeit - a['zeitstempel'] < 600
        ]

    def alarm_bestaetigen(self, sensor_id: str, alarm_typ: str) -> bool:
        """
        Bestätigt einen Alarm (entfernt aus aktiver Liste).

        @param sensor_id Sensor-ID
        @param alarm_typ Alarm-Typ
        @return True wenn gefunden und entfernt
        """
        for alarm in self._aktive_alarme:
            if alarm['sensor_id'] == sensor_id and alarm['alarm_typ'] == alarm_typ:
                self._aktive_alarme.remove(alarm)
                return True
        return False


class AlarmEngine:
    """
    Alarm-Engine für automatische Überwachung und Alarmierung.
    Nutzt das Observer/Notifier-Pattern für Alarmierung.
    """

    def __init__(self):
        """Initialisiert die Alarm-Engine mit allen Notifiern."""
        # Notifier-Liste erstellen
        self._notifier: List[AlarmNotifier] = []

        # Notifier instanziieren und registrieren
        self._registriere_notifier()

        # Letzten Alarm speichern um Spam zu vermeiden
        self.letzter_alarm_zeit = {}
        self.alarm_abstand_sekunden = 60  # Mindestens 60 Sekunden zwischen Alarmen

    def _registriere_notifier(self):
        """Registriert alle verfügbaren Notifier."""
        # E-Mail Notifier (mit Retry)
        self._notifier.append(EmailNotifier())

        # GPIO Notifier
        self._led_notifier = GPIOLedNotifier()
        self._buzzer_notifier = GPIOBuzzerNotifier()
        self._notifier.append(self._led_notifier)
        self._notifier.append(self._buzzer_notifier)

        # Dashboard Notifier
        self._dashboard_notifier = DashboardNotifier()
        self._notifier.append(self._dashboard_notifier)

    def initialisiere_gpio(self):
        """
        Initialisiert die GPIO-Pins für LED und Buzzer.

        @note Raspberry Pi spezifisch - wird auf anderen Systemen ignoriert
        """
        if not GPIO_VERFUEGBAR:
            logger.info("GPIO nicht verfügbar (kein Raspberry Pi)")
            return

        try:
            self._led_notifier.initialisiere()
            self._buzzer_notifier.initialisiere()
        except Exception as e:
            logger.warning(f"GPIO Initialisierung fehlgeschlagen: {e}")

    def hole_notifier(self, name: str) -> Optional[AlarmNotifier]:
        """
        Gibt einen Notifier anhand seines Namens zurück.

        @param name Name des Notifiers
        @return Notifier oder None
        """
        for notifier in self._notifier:
            if notifier.name == name:
                return notifier
        return None

    def hole_aktive_alarme(self) -> List[dict]:
        """Gibt aktive Alarme für Dashboard zurück."""
        return self._dashboard_notifier.aktive_alarme

    def alarm_bestaetigen(self, sensor_id: str, alarm_typ: str) -> bool:
        """Bestätigt einen Alarm im Dashboard."""
        return self._dashboard_notifier.alarm_bestaetigen(sensor_id, alarm_typ)

    def pruefe_alarm(self, sensor_id: str, sensor_typ: str, wert: float) -> Optional[dict]:
        """
        Prüft einen Messwert gegen Schwellwerte.

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
        Löst die Alarmierung aus über alle registrierten Notifier.

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

        # 2. Alle Notifier aufrufen (Exception-Handling pro Notifier)
        for notifier in self._notifier:
            try:
                ergebnis = notifier.senden(alarm)
                if not ergebnis:
                    logger.warning(f"{notifier.name}-Notifier: Versand fehlgeschlagen")
            except Exception as e:
                # Ein fehlgeschlagener Notifier blockiert nicht die anderen
                logger.error(f"{notifier.name}-Notifier Exception: {e}")

    def cleanup(self):
        """
        Räumt GPIO-Pins auf beim Beenden.

        @note Raspberry Pi spezifisch
        """
        if GPIO_VERFUEGBAR:
            try:
                GPIO.cleanup()
                logger.info("GPIO aufgeräumt")
            except Exception as e:
                logger.error(f"GPIO Cleanup Fehler: {e}")


# Globale Alarm-Instanz
alarm_engine = AlarmEngine()
