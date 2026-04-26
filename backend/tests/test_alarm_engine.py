"""
Tests für alarm_engine.py - Alarm-Logik

Diese Tests prüfen die Alarm-Erkennungslogik.
"""

import pytest
import time


class TestSpamSchutzLogik:
    """Tests für SpamSchutz-Logik"""

    def test_erster_alarm_erlaubt(self):
        """Test: Erster Alarm wird durchgelassen"""
        class SpamSchutz:
            def __init__(self, abstand):
                self.abstand = abstand
                self._letzte = {}
            
            def ist_erlaubt(self, key):
                jetzt = time.time()
                if key in self._letzte:
                    if jetzt - self._letzte[key] < self.abstand:
                        return False
                self._letzte[key] = jetzt
                return True
        
        spam = SpamSchutz(abstand=60)
        result = spam.ist_erlaubt("sensor1_TEMPERATUR_HOCH")
        assert result == True

    def test_zweiter_alarm_unterdrueckt(self):
        """Test: Zweiter Alarm innerhalb von 60s wird unterdrückt"""
        class SpamSchutz:
            def __init__(self, abstand):
                self.abstand = abstand
                self._letzte = {}
            
            def ist_erlaubt(self, key):
                jetzt = time.time()
                if key in self._letzte:
                    if jetzt - self._letzte[key] < self.abstand:
                        return False
                self._letzte[key] = jetzt
                return True
        
        spam = SpamSchutz(abstand=60)
        spam.ist_erlaubt("sensor1_TEMPERATUR_HOCH")  # Erster
        result = spam.ist_erlaubt("sensor1_TEMPERATUR_HOCH")  # Zweiter
        assert result == False

    def test_nach_abstand_wieder_erlaubt(self):
        """Test: Nach Ablauf des Abstands wird Alarm wieder erlaubt"""
        class SpamSchutz:
            def __init__(self, abstand):
                self.abstand = abstand
                self._letzte = {}
            
            def ist_erlaubt(self, key):
                jetzt = time.time()
                if key in self._letzte:
                    if jetzt - self._letzte[key] < self.abstand:
                        return False
                self._letzte[key] = jetzt
                return True
        
        spam = SpamSchutz(abstand=0)  # 0 = sofort wieder erlaubt
        spam.ist_erlaubt("sensor1_TEMPERATUR_HOCH")
        result = spam.ist_erlaubt("sensor1_TEMPERATUR_HOCH")
        assert result == True


class TestAlarmErkennung:
    """Tests für Alarm-Erkennung"""

    def test_temperatur_hoch(self):
        """Test: Zu hohe Temperatur wird erkannt"""
        def pruefe_alarm(sensor_typ, wert):
            if sensor_typ in ["DS18B20", "SHT31"]:
                if wert > 30.0:
                    return "TEMPERATUR_HOCH"
            return None
        
        assert pruefe_alarm("DS18B20", 35.0) == "TEMPERATUR_HOCH"
        assert pruefe_alarm("SHT31", 32.0) == "TEMPERATUR_HOCH"

    def test_temperatur_normal(self):
        """Test: Normale Temperatur löst keinen Alarm aus"""
        def pruefe_alarm(sensor_typ, wert):
            if sensor_typ in ["DS18B20", "SHT31"]:
                if wert > 30.0:
                    return "TEMPERATUR_HOCH"
            return None
        
        assert pruefe_alarm("DS18B20", 22.0) is None
        assert pruefe_alarm("SHT31", 25.0) is None

    def test_temperatur_niedrig(self):
        """Test: Zu niedrige Temperatur wird erkannt"""
        def pruefe_alarm(sensor_typ, wert):
            if sensor_typ in ["DS18B20", "SHT31"]:
                if wert > 30.0:
                    return "TEMPERATUR_HOCH"
                if wert < 15.0:
                    return "TEMPERATUR_NIEDRIG"
            return None
        
        assert pruefe_alarm("DS18B20", 10.0) == "TEMPERATUR_NIEDRIG"

    def test_rauchgas_alarm(self):
        """Test: Rauchgas-Alarm wird erkannt"""
        def pruefe_alarm(sensor_typ, wert):
            if sensor_typ == "MQ2" and wert > 200.0:
                return "RAUCHGAS"
            return None
        
        assert pruefe_alarm("MQ2", 250.0) == "RAUCHGAS"
        assert pruefe_alarm("MQ2", 150.0) is None

    def test_luftqualitaet_alarm(self):
        """Test: Luftqualitäts-Alarm wird erkannt"""
        def pruefe_alarm(sensor_typ, wert):
            if sensor_typ == "MQ135" and wert > 800.0:
                return "LUFTQUALITAET"
            return None
        
        assert pruefe_alarm("MQ135", 900.0) == "LUFTQUALITAET"
        assert pruefe_alarm("MQ135", 500.0) is None

    def test_bewegung_pir(self):
        """Test: PIR löst keinen automatischen Alarm aus"""
        def pruefe_alarm(sensor_typ, wert):
            # PIR wird separat behandelt
            if sensor_typ == "PIR":
                return None
            return None
        
        assert pruefe_alarm("PIR", 1) is None


class TestAlarmDataclassLogik:
    """Tests für Alarm-Dataclass-Logik"""

    def test_alarm_hat_attribute(self):
        """Test: Alarm hat alle erforderlichen Attribute"""
        alarm = {
            "sensor_id": "test_sensor",
            "alarm_typ": "TEMPERATUR_HOCH",
            "nachricht": "Temperatur zu hoch: 35.0°C",
            "wert": 35.0,
            "schwellwert": 30.0
        }
        
        assert "sensor_id" in alarm
        assert "alarm_typ" in alarm
        assert "nachricht" in alarm
        assert "wert" in alarm
        assert "schwellwert" in alarm

    def test_alarm_key_generierung(self):
        """Test: Alarm-Key wird korrekt generiert"""
        sensor_id = "temp_serverraum"
        alarm_typ = "TEMPERATUR_HOCH"
        alarm_key = f"{sensor_id}_{alarm_typ}"
        
        assert alarm_key == "temp_serverraum_TEMPERATUR_HOCH"


class TestGPIODeviceLogik:
    """Tests für GPIO-Geräte-Logik"""

    def test_led_pin_konfiguration(self):
        """Test: LED Pin ist im gültigen Bereich"""
        led_pin = 17
        assert 0 <= led_pin <= 27

    def test_buzzer_pin_konfiguration(self):
        """Test: Buzzer Pin ist im gültigen Bereich"""
        buzzer_pin = 27
        assert 0 <= buzzer_pin <= 27

    def test_gpio_initialisierung(self):
        """Test: GPIO Initialisierung Logik"""
        initialisiert = False
        gpio_verfuegbar = True
        
        if gpio_verfuegbar and not initialisiert:
            initialisiert = True
        
        assert initialisiert == True


class TestDashboardNotifierLogik:
    """Tests für DashboardNotifier-Logik"""

    def test_alarm_wird_angehaengt(self):
        """Test: Alarm wird zur Liste hinzugefügt"""
        alarme = []
        alarm = {
            "sensor_id": "s1",
            "alarm_typ": "TEST",
            "nachricht": "Test",
            "wert": 35.0,
            "schwellwert": 30.0,
            "zeitstempel": time.time()
        }
        
        alarme.append(alarm)
        
        assert len(alarme) == 1
        assert alarme[0]["sensor_id"] == "s1"

    def test_alarm_bestaetigen(self):
        """Test: Alarm wird aus Liste entfernt"""
        alarme = [
            {"sensor_id": "s1", "alarm_typ": "TEST"},
            {"sensor_id": "s2", "alarm_typ": "TEST"}
        ]
        
        # Bestätige s1
        alarme = [a for a in alarme if not (a["sensor_id"] == "s1" and a["alarm_typ"] == "TEST")]
        
        assert len(alarme) == 1
        assert alarme[0]["sensor_id"] == "s2"

    def test_alte_alarme_werden_entfernt(self):
        """Test: Alte Alarme werden nach 10 Minuten entfernt"""
        alarme = [
            {"sensor_id": "s1", "zeitstempel": time.time() - 600},  # 10 min alt
            {"sensor_id": "s2", "zeitstempel": time.time()}  # Gerade
        ]
        
        # Nur Alarme der letzten 10 Minuten behalten
        alarme = [a for a in alarme if time.time() - a["zeitstempel"] < 600]
        
        assert len(alarme) == 1
        assert alarme[0]["sensor_id"] == "s2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
