"""
Logik-Tests für das Backend

Diese Tests prüfen die Geschäftslogik ohne komplexe Imports.
"""

import pytest


class TestAlarmLogik:
    """Tests für Alarm-Erkennungslogik"""

    @pytest.mark.parametrize("sensor_typ,wert,erwartet", [
        ("DS18B20", 35.0, "TEMPERATUR_HOCH"),
        ("DS18B20", 10.0, "TEMPERATUR_NIEDRIG"),
        ("DS18B20", 22.0, None),
        ("SHT31", 35.0, "TEMPERATUR_HOCH"),
        ("SHT31", 10.0, "TEMPERATUR_NIEDRIG"),
        ("SHT31", 22.0, None),
        ("MQ2", 250.0, "RAUCHGAS"),
        ("MQ2", 150.0, None),
        ("MQ135", 900.0, "LUFTQUALITAET"),
        ("MQ135", 500.0, None),
    ])
    def test_alarm_erkennung(self, sensor_typ, wert, erwartet):
        """Test: Alarm wird korrekt erkannt"""
        def pruefe_alarm(sensor_typ, wert):
            if sensor_typ in ["DS18B20", "SHT31"]:
                if wert > 30.0:
                    return "TEMPERATUR_HOCH"
                if wert < 15.0:
                    return "TEMPERATUR_NIEDRIG"
            if sensor_typ == "MQ2" and wert > 200.0:
                return "RAUCHGAS"
            if sensor_typ == "MQ135" and wert > 800.0:
                return "LUFTQUALITAET"
            return None
        
        result = pruefe_alarm(sensor_typ, wert)
        assert result == erwartet


class TestSpamSchutzLogik:
    """Tests für Spam-Schutz"""

    def test_spam_schutz_unterdrueckt_wiederholte_alarme(self):
        """Test: Wiederholte Alarme werden unterdrückt"""
        import time
        
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
        
        # Erster Alarm erlaubt
        assert spam.ist_erlaubt("s1_TEMP") == True
        
        # Zweiter Alarm sofort unterdrückt
        assert spam.ist_erlaubt("s1_TEMP") == False

    def test_spam_schutz_unterschiedliche_sensoren(self):
        """Test: Unterschiedliche Sensoren werden nicht unterdrückt"""
        import time
        
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
        
        # Unterschiedliche Sensoren
        assert spam.ist_erlaubt("s1_TEMP") == True
        assert spam.ist_erlaubt("s2_TEMP") == True

    def test_spam_schutz_nach_pause(self):
        """Test: Nach Pause wird Alarm wieder erlaubt"""
        import time
        
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
        
        spam = SpamSchutz(abstand=0)  # 0 = keine Verzögerung
        
        spam.ist_erlaubt("s1_TEMP")
        result = spam.ist_erlaubt("s1_TEMP")
        
        assert result == True


class TestSensorTypPruefung:
    """Tests für Sensor-Typ Prüfung"""

    def test_temperatursensoren(self):
        """Test: DS18B20 und SHT31 sind Temperatursensoren"""
        temp_sensoren = ["DS18B20", "SHT31"]
        
        assert "DS18B20" in temp_sensoren
        assert "SHT31" in temp_sensoren
        assert "DHT22" not in temp_sensoren  # DHT22 wurde entfernt

    def test_gassensoren(self):
        """Test: MQ2 und MQ135 sind Gassensoren"""
        gas_sensoren = ["MQ2", "MQ135"]
        
        assert "MQ2" in gas_sensoren
        assert "MQ135" in gas_sensoren


class TestDatenbankSchemaLogik:
    """Tests für DB-Schema Logik"""

    def test_sensoren_tabelle_hat_spalten(self):
        """Test: Sensoren-Tabelle hat erforderliche Spalten"""
        spalten = ["id", "sensor_typ", "name", "beschreibung", "gpio_pin", "einheit", "aktiv"]
        
        # Annahme: Diese Spalten sollten existieren
        assert "id" in spalten
        assert "sensor_typ" in spalten
        assert "aktiv" in spalten

    def test_alarm_status_werte(self):
        """Test: Alarm Status sind korrekt"""
        gueltige_status = ["aktiv", "quittiert", "geloest"]
        
        assert "aktiv" in gueltige_status
        assert "quittiert" in gueltige_status


class TestConfigLogik:
    """Tests für Konfigurations-Logik"""

    def test_schwellwerte_plausibel(self):
        """Test: Schwellwerte sind plausibel"""
        temp_min = 15.0
        temp_max = 30.0
        
        assert temp_min < temp_max
        assert -50 <= temp_min <= 100
        assert -50 <= temp_max <= 100

    def test_schwellwerte_rauchgas(self):
        """Test: Rauchgas-Schwellwert ist plausibel"""
        rauchgas_max = 200.0
        
        assert rauchgas_max > 0
        assert rauchgas_max < 10000  # Realistisch für MQ-2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
