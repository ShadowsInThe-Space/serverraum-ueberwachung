"""
Pytest Fixtures und Konfiguration für Tests
"""

import pytest
import os
import sys

# Pfad zum Backend hinzufügen
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test-Konfiguration
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "3306"
os.environ["DB_USER"] = "backend_user"
os.environ["DB_PASS"] = "backend123"
os.environ["DB_NAME"] = "serverraum_ueberwachung"
os.environ["MQTT_BROKER"] = "localhost"
os.environ["MQTT_PORT"] = "1883"


@pytest.fixture
def test_sensor_data():
    """Test-Daten für Sensoren"""
    return {
        "sensor_id": "test_sensor_001",
        "sensor_typ": "SHT31",
        "name": "Test Sensor",
        "wert": 22.5,
        "status": "OK"
    }


@pytest.fixture
def test_alarm_data():
    """Test-Daten für Alarme"""
    return {
        "sensor_id": "test_sensor_001",
        "alarm_typ": "TEMPERATUR_HOCH",
        "nachricht": "Temperatur zu hoch: 35.0°C",
        "wert": 35.0,
        "schwellwert": 30.0
    }
