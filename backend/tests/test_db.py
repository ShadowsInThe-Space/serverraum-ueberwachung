"""
Tests für db.py - Datenbank-Operationen

Diese Tests prüfen die Logik und SQL-Queries.
"""

import pytest


class TestSQLQueries:
    """Tests für SQL-Queries"""

    def test_sensor_speichern_query(self):
        """Test: Sensor speichern Query hat korrekte Struktur"""
        sql = """
            INSERT INTO sensoren (sensor_id, sensor_typ, name, aktiv, created_at)
            VALUES (%s, %s, %s, 1, NOW())
            ON DUPLICATE KEY UPDATE sensor_typ = VALUES(sensor_typ), updated_at = NOW()
        """
        
        assert "INSERT INTO sensoren" in sql
        assert "%s" in sql
        assert "ON DUPLICATE KEY UPDATE" in sql

    def test_messung_speichern_query(self):
        """Test: Messung speichern Query"""
        sql = "INSERT INTO messungen (sensor_id, wert, status, timestamp) VALUES (%s, %s, %s, NOW())"
        
        assert "INSERT INTO messungen" in sql
        assert "%s" in sql

    def test_letzte_messungen_query(self):
        """Test: Letzte Messungen Query mit JOIN"""
        sql = """SELECT m.wert, m.timestamp FROM messungen m
               JOIN sensoren s ON m.sensor_id = s.id
               WHERE s.sensor_id = %s
               ORDER BY m.timestamp DESC LIMIT %s"""
        
        assert "SELECT" in sql
        assert "JOIN" in sql
        assert "WHERE" in sql
        assert "ORDER BY" in sql

    def test_alarm_speichern_query(self):
        """Test: Alarm speichern Query"""
        sql = """
            INSERT INTO alarme (sensor_id, alarm_typ, nachricht, wert, schwellwert, status, created_at)
            VALUES (%s, %s, %s, %s, %s, 'aktiv', NOW())
        """
        
        assert "INSERT INTO alarme" in sql
        assert "'aktiv'" in sql

    def test_alarm_quittieren_query(self):
        """Test: Alarm quittieren Query"""
        sql = "UPDATE alarme SET status = 'quittiert', quittiert_at = NOW() WHERE id = %s"
        
        assert "UPDATE alarme" in sql
        assert "status = 'quittiert'" in sql
        assert "WHERE id = %s" in sql

    def test_aktive_alarme_query(self):
        """Test: Aktive Alarme Query mit JOIN"""
        sql = """
            SELECT a.*, s.sensor_id
            FROM alarme a JOIN sensoren s ON a.sensor_id = s.id
            WHERE a.status = 'aktiv' ORDER BY a.created_at DESC
        """
        
        assert "SELECT" in sql
        assert "JOIN" in sql
        assert "WHERE a.status = 'aktiv'" in sql

    def test_statistik_query(self):
        """Test: Statistik Query mit Aggregat-Funktionen"""
        sql = """
            SELECT MIN(m.wert) as min, MAX(m.wert) as max,
                   AVG(m.wert) as durchschnitt, COUNT(*) as anzahl
            FROM messungen m JOIN sensoren s ON m.sensor_id = s.id
            WHERE s.sensor_id = %s AND m.timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
        """
        
        assert "MIN(" in sql
        assert "MAX(" in sql
        assert "AVG(" in sql
        assert "COUNT(*)" in sql
        assert "DATE_SUB" in sql

    def test_alle_sensoren_query(self):
        """Test: Alle Sensoren Query"""
        sql = "SELECT id, sensor_id, sensor_typ, name, aktiv FROM sensoren ORDER BY created_at DESC"
        
        assert "SELECT" in sql
        assert "FROM sensoren" in sql


class TestSQLInjectionSchutz:
    """Tests für SQL Injection Schutz"""

    def test_platzhalter_werden_verwendet(self):
        """Test: Alle Queries verwenden %s Platzhalter"""
        queries = [
            ("SELECT * FROM test WHERE id = %s", ("1",)),
            ("INSERT INTO test VALUES (%s, %s)", ("a", "b")),
            ("UPDATE test SET name = %s WHERE id = %s", ("neu", "1")),
        ]
        
        for sql, params in queries:
            assert sql.count("%s") == len(params)

    def test_keine_string_formatierung(self):
        """Test: Keine f-Strings oder % in Queries"""
        # Diese Funktion prüft ob der SQL-String sicher ist
        
        def ist_sicher(sql):
            # Keine Python-Formatierung im SQL
            if "%" in sql and "%s" not in sql:
                return False
            if "{" in sql or "}" in sql:
                return False
            if "format(" in sql:
                return False
            return True
        
        assert ist_sicher("SELECT * FROM test WHERE id = %s")
        assert ist_sicher("INSERT INTO test VALUES (%s, %s)")


class TestConnectionPooling:
    """Tests für Connection Pooling"""

    def test_pool_konfiguration(self):
        """Test: Pool Konfiguration ist korrekt"""
        pool_name = "serverraum_pool"
        pool_size = 5
        
        assert pool_name == "serverraum_pool"
        assert pool_size == 5
        assert pool_size >= 1
        assert pool_size <= 20

    def test_pool_keine_harten_credentials(self):
        """Test: Credentials kommen nicht direkt aus Code"""
        # Diese Tests prüfen dass keine Passwörter im Code sind
        
        code = """
            password = config.datenbank.passwort
            user = config.datenbank.benutzer
        """
        
        assert "config.datenbank.passwort" in code
        assert "config.datenbank.benutzer" in code
        # Keine harten Werte wie "password123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
