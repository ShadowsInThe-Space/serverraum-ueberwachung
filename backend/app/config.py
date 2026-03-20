"""
Konfigurationsdatei für das Backend
===================================

Enthält alle Einstellungen für:
- MQTT Broker
- MariaDB Datenbank
- Alarmierung
- REST-API

Verwendet Pydantic Settings für automatisiertes Laden aus .env
und Environment Variables.

@author Marc-Dennis Haberland
@date 20.03.2026
Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator
from typing import Optional


class MqttConfig(BaseSettings):
    """MQTT Broker Konfiguration"""
    broker: str = "192.168.178.48"
    port: int = Field(default=1883, ge=1, le=65535)
    client_id: str = "serverraum_backend"
    topic_basis: str = "serverraum/sensor"
    # QoS Level: 0 = einmal senden, 1 = mindestens einmal, 2 = genau einmal
    qos: int = Field(default=1, ge=0, le=2)

    model_config = SettingsConfigDict(env_prefix="MQTT_")


class DatabaseConfig(BaseSettings):
    """MariaDB Datenbank Konfiguration"""
    host: str = "localhost"
    port: int = Field(default=3306, ge=1, le=65535)
    benutzer: str = "serverraum"
    passwort: str = Field(default="", env="DB_PASS")
    datenbank: str = "serverraum_ueberwachung"

    model_config = SettingsConfigDict(env_prefix="DB_")


class AlarmConfig(BaseSettings):
    """Alarmierung Konfiguration"""
    # E-Mail Einstellungen
    email_enabled: bool = True
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = Field(default=587, ge=1, le=65535)
    email_absender: str = "serverraum@example.com"
    email_passwort: str = Field(default="", env="EMAIL_PASS")
    email_empfaenger: str = "admin@example.com"

    # Warn-LED (GPIO Pin am Raspberry Pi)
    led_enabled: bool = True
    led_pin: int = Field(default=17, ge=0, le=27)

    # Buzzer
    buzzer_enabled: bool = True
    buzzer_pin: int = Field(default=27, ge=0, le=27)

    # Alarm-Schwellwerte
    temperatur_max: float = Field(default=30.0, ge=-50, le=100)
    temperatur_min: float = Field(default=15.0, ge=-50, le=100)
    rauchgas_max: float = Field(default=200.0, ge=0)
    luftqualitaet_max: float = Field(default=800.0, ge=0)

    @model_validator(mode="after")
    def validate_temperatur_schwellwerte(self) -> "AlarmConfig":
        """Validiert dass temperatur_min < temperatur_max"""
        if self.temperatur_min >= self.temperatur_max:
            raise ValueError(
                f"temperatur_min ({self.temperatur_min}) muss kleiner als "
                f"temperatur_max ({self.temperatur_max}) sein"
            )
        return self

    model_config = SettingsConfigDict(env_prefix="ALARM_")


class ApiConfig(BaseSettings):
    """REST-API Konfiguration"""
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    debug: bool = False

    model_config = SettingsConfigDict(env_prefix="API_")


class Config(BaseSettings):
    """Hauptkonfiguration - fasst alle Teil-Konfigurationen zusammen"""
    mqtt: MqttConfig = Field(default_factory=MqttConfig)
    datenbank: DatabaseConfig = Field(default_factory=DatabaseConfig)
    alarm: AlarmConfig = Field(default_factory=AlarmConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore"
    )


# Globale Konfigurations-Instanz
# Wird beim Start geladen und im Programm verwendet
config = Config()


def lade_konfiguration_aus_env():
    """
    Lädt Konfiguration aus Umgebungsvariablen
    (Nicht mehr nötig - Pydantic lädt automatisch)

    Diese Funktion bleibt für Abwärtskompatibilität.
    """
    # Pydantic lädt bereits automatisch aus .env und Environment Variables
    # Hier nichts weiter zu tun
    pass


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
    print(f"\n  E-Mail Alarm: {'Aktiviert' if config.alarm.email_enabled else 'Deaktiviert'}")
    print(f"  LED Alarm: {'Aktiviert (Pin ' + str(config.alarm.led_pin) + ')' if config.alarm.led_enabled else 'Deaktiviert'}")
    print(f"  Buzzer Alarm: {'Aktiviert (Pin ' + str(config.alarm.buzzer_pin) + ')' if config.alarm.buzzer_enabled else 'Deaktiviert'}")
