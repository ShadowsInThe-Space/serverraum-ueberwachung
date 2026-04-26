"""
Alarm-Engine für Serverraum-Überwachung
=======================================

Vereinfachte Version:
- GPIO-Notifier zusammengefasst (LED + Buzzer)
- Dataclass für Alarm
- Klare Trennung: Prüfung → Alarm-Erstellung → Notifizierung

@author Marc-Dennis Haberland
@date 14.03.2026
"""

import logging
import smtplib
import time
import threading
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

try:
    import RPi.GPIO as GPIO

    GPIO_VERFUEGBAR = True
except ImportError:
    GPIO_VERFUEGBAR = False

from .config import config
from .db import datenbank

logger = logging.getLogger(__name__)


@dataclass
class Alarm:
    """Einfacher Alarm-Dataclass statt Dictionary-Soup"""

    sensor_id: str
    alarm_typ: str
    nachricht: str
    wert: float
    schwellwert: float
    id: Optional[int] = None


class SpamSchutz:
    """Simpler Spam-Schutz mit Zeitstempel-Dict"""

    def __init__(self, abstand_sekunden: int = 60):
        self.abstand = abstand_sekunden
        self._letzte_alarme: dict[str, float] = {}

    def ist_erlaubt(self, alarm_key: str) -> bool:
        jetzt = time.time()
        if alarm_key in self._letzte_alarme:
            if jetzt - self._letzte_alarme[alarm_key] < self.abstand:
                return False
        self._letzte_alarme[alarm_key] = jetzt
        return True


# =============================================================================
# NOTIFIER
# =============================================================================


class EmailNotifier:
    """E-Mail mit Retry - nur das Notwendigste"""

    def __init__(self):
        self.enabled = config.alarm.email_enabled
        self.empfaenger = config.alarm.email_empfaenger
        self.absender = config.alarm.email_absender
        self.passwort = config.alarm.email_passwort
        self.server = config.alarm.email_smtp_server
        self.port = config.alarm.email_smtp_port

    def senden(self, alarm: Alarm) -> bool:
        if not self.enabled:
            return True

        # Email in DB speichern (ausstehend)
        email_id = datenbank.alarm_email_speichern(
            alarm_id=alarm.id,
            empfaenger=self.empfaenger,
            subject=f"⚠️ Serverraum Alarm: {alarm.alarm_typ}",
            body=f"{alarm.nachricht}\nSensor: {alarm.sensor_id}\nWert: {alarm.wert}\nSchwellwert: {alarm.schwellwert}",
            sende_status='ausstehend'
        )

        fehler = None
        for versuch in range(3):
            try:
                success = self._sende(alarm)
                if success:
                    datenbank.alarm_email_aktualisieren(email_id, 'erfolgreich')
                    return True
            except Exception as e:
                fehler = e
                logger.warning(f"E-Mail Fehler (Versuch {versuch + 1}): {e}")
                if versuch < 2:
                    time.sleep(2)

        # Fehlgeschlagen in DB speichern
        datenbank.alarm_email_aktualisieren(email_id, 'fehlgeschlagen', str(fehler))
        logger.error("E-Mail Alarm fehlgeschlagen")
        return False

    def _sende(self, alarm: Alarm) -> bool:
        nachricht = MIMEMultipart("alternative")
        nachricht["Subject"] = f"⚠️ Serverraum Alarm: {alarm.alarm_typ}"
        nachricht["From"] = self.absender
        nachricht["To"] = self.empfaenger

        text = f"""Serverraum-Überwachung - ALARM

{alarm.nachricht}
Sensor: {alarm.sensor_id}
Wert: {alarm.wert}
Schwellwert: {alarm.schwellwert}
"""
        nachricht.attach(MIMEText(text, "plain"))
        nachricht.attach(MIMEText(f"<p>{alarm.nachricht}</p>", "html"))

        with smtplib.SMTP(self.server, self.port) as server:
            server.starttls()
            server.login(self.absender, self.passwort)
            server.sendmail(self.absender, self.empfaenger, nachricht.as_string())

        logger.info(f"E-Mail gesendet an {self.empfaenger}")
        return True


class GPIODeviceNotifier:
    """LED + Buzzer in EINER Klasse - kein Duplikat mehr"""

    def __init__(self, pin: int, aktion: str, dauer: float):
        self.pin = pin
        self.aktion = aktion  # "LED" oder "BUZZER"
        self.dauer = dauer  # 5.0 für LED, 2.0 für Buzzer
        self._initialisiert = False

    def initialisiere(self):
        if self._initialisiert or not GPIO_VERFUEGBAR:
            return

        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.OUT, initial=GPIO.LOW)
            self._initialisiert = True
            logger.info(f"{self.aktion} initialisiert: GPIO {self.pin}")
        except Exception as e:
            logger.warning(f"{self.aktion} Init-Fehler: {e}")

    def senden(self, alarm: Alarm) -> bool:
        if not self._initialisiert:
            return True

        try:
            GPIO.output(self.pin, GPIO.HIGH)
            threading.Timer(self.dauer, lambda: self._ausschalten()).start()
            return True
        except Exception as e:
            logger.error(f"{self.aktion} Fehler: {e}")
            return False

    def _ausschalten(self):
        try:
            GPIO.output(self.pin, GPIO.LOW)
        except Exception:
            pass


class DashboardNotifier:
    """Speichert aktive Alarme in Liste"""

    def __init__(self):
        self._alarme: list[dict] = []

    def senden(self, alarm: Alarm) -> bool:
        self._alarme.append(
            {
                "sensor_id": alarm.sensor_id,
                "alarm_typ": alarm.alarm_typ,
                "nachricht": alarm.nachricht,
                "wert": alarm.wert,
                "schwellwert": alarm.schwellwert,
                "zeitstempel": time.time(),
            }
        )
        # Aufräumen: nur Alarme der letzten 10 Min
        self._alarme = [a for a in self._alarme if time.time() - a["zeitstempel"] < 600]
        return True

    def bestaetigen(self, sensor_id: str, alarm_typ: str) -> bool:
        for alarm in self._alarme:
            if alarm["sensor_id"] == sensor_id and alarm["alarm_typ"] == alarm_typ:
                self._alarme.remove(alarm)
                return True
        return False


# =============================================================================
# ALARM ENGINE
# =============================================================================


class AlarmEngine:
    """Hauptklasse - jetzt mit klarer Struktur"""

    def __init__(self):
        self._spam = SpamSchutz(abstand_sekunden=60)

        # Notifier erstellen
        self._notifier = [
            EmailNotifier(),
            GPIODeviceNotifier(config.alarm.led_pin, "LED", 5.0),
            GPIODeviceNotifier(config.alarm.buzzer_pin, "BUZZER", 2.0),
            DashboardNotifier(),
        ]
        self._dashboard: DashboardNotifier = self._notifier[3]

    def initialisiere_gpio(self):
        if not GPIO_VERFUEGBAR:
            logger.info("GPIO nicht verfügbar")
            return
        for n in self._notifier:
            if isinstance(n, GPIODeviceNotifier):
                n.initialisiere()

    def pruefe_alarm(
        self, sensor_id: str, sensor_typ: str, wert: float
    ) -> Optional[Alarm]:
        """Prüft Schwellwerte und erstellt Alarm-Objekt"""

        # Temperatur
        if sensor_typ in ["DS18B20", "SHT31"]:
            if wert > config.alarm.temperatur_max:
                return Alarm(
                    sensor_id,
                    "TEMPERATUR_HOCH",
                    f"Temperatur zu hoch: {wert:.1f}°C",
                    wert,
                    config.alarm.temperatur_max,
                )
            if wert < config.alarm.temperatur_min:
                return Alarm(
                    sensor_id,
                    "TEMPERATUR_NIEDRIG",
                    f"Temperatur zu niedrig: {wert:.1f}°C",
                    wert,
                    config.alarm.temperatur_min,
                )

        # Rauchgas
        elif sensor_typ == "MQ2" and wert > config.alarm.rauchgas_max:
            return Alarm(
                sensor_id,
                "RAUCHGAS",
                f"Rauchgas: {wert:.0f} ppm",
                wert,
                config.alarm.rauchgas_max,
            )

        # Luftqualität
        elif sensor_typ == "MQ135" and wert > config.alarm.luftqualitaet_max:
            return Alarm(
                sensor_id,
                "LUFTQUALITAET",
                f"Luftqualität: {wert:.0f} ppm",
                wert,
                config.alarm.luftqualitaet_max,
            )

        return None

    def alarm_ausloesen(self, alarm: Alarm):
        """Löst Alarm aus - prüft Spam, speichert DB, benachrichtigt"""

        alarm_key = f"{alarm.sensor_id}_{alarm.alarm_typ}"

        # Spam-Schutz
        if not self._spam.ist_erlaubt(alarm_key):
            logger.debug(f"Alarm unterdrückt (Spam): {alarm_key}")
            return

        logger.warning(f"ALARM: {alarm.nachricht}")

        # DB speichern und ID merken für Email-Tracking
        alarm.id = datenbank.alarm_speichern(
            sensor_id=alarm.sensor_id,
            alarm_typ=alarm.alarm_typ,
            nachricht=alarm.nachricht,
            wert=alarm.wert,
            schwellwert=alarm.schwellwert,
        )

        # Alle Notifier
        for n in self._notifier:
            try:
                n.senden(alarm)
            except Exception as e:
                logger.error(f"{type(n).__name__} Fehler: {e}")

    # Convenience-Methoden
    def hole_aktive_alarme(self):
        return self._dashboard._alarme

    def alarm_bestaetigen(self, sensor_id: str, alarm_typ: str):
        return self._dashboard.bestaetigen(sensor_id, alarm_typ)

    def cleanup(self):
        if GPIO_VERFUEGBAR:
            GPIO.cleanup()


alarm_engine = AlarmEngine()
