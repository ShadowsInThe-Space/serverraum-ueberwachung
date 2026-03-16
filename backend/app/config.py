"""
Konfigurationsdatei für das Backend
===================================

Enthält alle Einstellungen für:
- MQTT Broker
- MariaDB Datenbank
- Alarmierung
- REST-API

@author Marc-Dennis Haberland
@date 04.03.2026
Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MqttConfig:
    """MQTT Broker Konfiguration"""
    broker: str = "localhost"
    port: int = 1883
    client_id: str = "serverraum_backend"
    topic_basis: str = "serverraum/sensor"
    # QoS Level: 0 = einmal senden, 1 = mindestens einmal, 2 = genau einmal
    qos: int = 1


@dataclass
class DatabaseConfig:
    """MariaDB Datenbank Konfiguration"""
    host: str = "localhost"
    port: int = 3306
    benutzer: str = "serverraum"
    passwort: str = ""  # Muss über DB_PASS Umgebungsvariable gesetzt werden
    datenbank: str = "serverraum_ueberwachung"


@dataclass
class AlarmConfig:
    """Alarmierung Konfiguration"""
    # E-Mail Einstellungen
    email_enabled: bool = True
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_absender: str = "serverraum@example.com"
    email_passwort: str = ""  # Muss über EMAIL_PASS Umgebungsvariable gesetzt werden
    email_empfaenger: str = "admin@example.com"

    # Warn-LED (GPIO Pin am Raspberry Pi)
    led_enabled: bool = True
    led_pin: int = 17

    # Buzzer
    buzzer_enabled: bool = True
    buzzer_pin: int = 27

    # Alarm-Schwellwerte
    temperatur_max: float = 30.0  # °C
    temperatur_min: float = 15.0  # °C
    rauchgas_max: float = 200.0   # ppm
    luftqualitaet_max: float = 800.0  # ppm CO2-Äquivalent


@dataclass
class ApiConfig:
    """REST-API Konfiguration"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False


def _default_mqtt():
    return MqttConfig()


def _default_database():
    return DatabaseConfig()


def _default_alarm():
    return AlarmConfig()


def _default_api():
    return ApiConfig()


@dataclass
class Config:
    """Hauptkonfiguration - fasst alle Teil-Konfigurationen zusammen"""
    mqtt: MqttConfig = field(default_factory=_default_mqtt)
    datenbank: DatabaseConfig = field(default_factory=_default_database)
    alarm: AlarmConfig = field(default_factory=_default_alarm)
    api: ApiConfig = field(default_factory=_default_api)


# Globale Konfigurations-Instanz
# Wird beim Start geladen und im Programm verwendet
config = Config()


def lade_konfiguration_aus_env():
    """
    Lädt Konfiguration aus Umgebungsvariablen
    Ermöglicht Deployment ohne Code-Änderung
    """
    import os

    # MQTT
    config.mqtt.broker = os.getenv("MQTT_BROKER", config.mqtt.broker)
    config.mqtt.port = int(os.getenv("MQTT_PORT", str(config.mqtt.port)))

    # Datenbank
    config.datenbank.host = os.getenv("DB_HOST", config.datenbank.host)
    config.datenbank.benutzer = os.getenv("DB_USER", config.datenbank.benutzer)
    config.datenbank.passwort = os.getenv("DB_PASS", config.datenbank.passwort)
    config.datenbank.datenbank = os.getenv("DB_NAME", config.datenbank.datenbank)

    # API
    config.api.port = int(os.getenv("API_PORT", str(config.api.port)))
    config.api.debug = os.getenv("DEBUG", "false").lower() == "true"


if __name__ == "__main__":
    # Testausgabe der Konfiguration
    print("=== Serverraum-Überwachung Backend Konfiguration ===")
    print(f"\nMQTT Broker: {config.mqtt.broker}:{config.mqtt.port}")
    print(f"Datenbank: {config.datenbank.host}/{config.datenbank.datenbank}")
    print(f"API: {config.api.host}:{config.api.port}")
    print(f"\nAlarm-Schwellwerte:")
    print(f"  Temperatur: {config.alarm.temperatur_min}°C - {config.alarm.temperatur_max}°C")
    print(f"  Rauchgas: {config.alarm.rauchgas_max} ppm")
    print(f"  Luftqualität: {config.alarm.luftqualitaet_max} ppm")
