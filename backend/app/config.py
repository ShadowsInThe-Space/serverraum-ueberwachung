"""
Konfiguration für Backend
========================

Lädt automatisch aus .env und Environment Variables.

@author Marc-Dennis Haberland
@date 20.03.2026
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class MqttConfig(BaseSettings):
    broker: str = Field(default="localhost", env="MQTT_BROKER")
    port: int = Field(default=1883, ge=1, le=65535)
    client_id: str = "serverraum_backend"
    topic_basis: str = "serverraum/sensor"
    qos: int = Field(default=1, ge=0, le=2)

    model_config = SettingsConfigDict(env_prefix="MQTT_")


class DatabaseConfig(BaseSettings):
    host: str = "localhost"
    port: int = Field(default=3306, ge=1, le=65535)
    benutzer: str = Field(default="backend_user", env="DB_USER")
    passwort: str = Field(default="backend123", env="DB_PASS")
    datenbank: str = "serverraum_ueberwachung"

    model_config = SettingsConfigDict(env_prefix="DB_")


class AlarmConfig(BaseSettings):
    # E-Mail
    email_enabled: bool = True
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = Field(default=587, ge=1, le=65535)
    email_absender: str = "serverraum@example.com"
    email_passwort: str = Field(default="", env="EMAIL_PASS")
    email_empfaenger: str = "admin@example.com"

    # Google API
    google_api_key: str = Field(default="", env="GOOGLE_API_KEY")

    # GPIO
    led_enabled: bool = True
    led_pin: int = Field(default=17, ge=0, le=27)
    buzzer_enabled: bool = True
    buzzer_pin: int = Field(default=27, ge=0, le=27)

    # Schwellwerte
    temperatur_max: float = Field(default=30.0, ge=-50, le=100)
    temperatur_min: float = Field(default=15.0, ge=-50, le=100)
    rauchgas_max: float = Field(default=200.0, ge=0)
    luftqualitaet_max: float = Field(default=800.0, ge=0)

    model_config = SettingsConfigDict(env_prefix="ALARM_")


class ApiConfig(BaseSettings):
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    debug: bool = False

    model_config = SettingsConfigDict(env_prefix="API_")


class Config(BaseSettings):
    mqtt: MqttConfig = Field(default_factory=MqttConfig)
    datenbank: DatabaseConfig = Field(default_factory=DatabaseConfig)
    alarm: AlarmConfig = Field(default_factory=AlarmConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


config = Config()


if __name__ == "__main__":
    print("=== Konfiguration ===")
    print(f"MQTT: {config.mqtt.broker}:{config.mqtt.port}")
    print(f"DB: {config.datenbank.host}/{config.datenbank.datenbank}")
    print(f"API: {config.api.host}:{config.api.port}")
    print(f"Temp: {config.alarm.temperatur_min}°C - {config.alarm.temperatur_max}°C")
