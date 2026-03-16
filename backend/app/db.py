"""
Datenbank-Modul für MariaDB-Anbindung
=====================================

Verwaltet die Verbindung zur MariaDB Datenbank und führt
SQL-Operationen für Sensor-Daten und Alarme durch.

Datenbank-Schema:
- sensoren: Konfiguration der Sensoren
- messungen: Sensor-Messwerte
- alarme: Alarm-Historie
- konfiguration: System-Einstellungen

@author Marc-Dennis Haberland
@date 04.03.2026
Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import mysql.connector
from mysql.connector import Error
from .config import config

# Logger konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _neue_verbindung():
    """Erstellt eine neue Datenbankverbindung"""
    import os
    try:
        conn = mysql.connector.connect(
            host=config.datenbank.host,
            port=config.datenbank.port,
            user=config.datenbank.benutzer,
            password=config.datenbank.passwort or os.getenv('DB_PASS', ''),
            database=config.datenbank.datenbank,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci',
            autocommit=True,
            connection_timeout=60
        )
        return conn
    except Error as e:
        logger.error(f"Verbindungsfehler: {e}")
        return None


class Datenbank:
    """
    Klasse für MariaDB Datenbank-Operationen
    Jede Methode erstellt ihre eigene Verbindung für Zuverlässigkeit.
    """

    def __init__(self):
        self.connection = None

    def verbinden(self):
        """Verbindet zur Datenbank (für Kompatibilität mit main.py)"""
        import os
        try:
            self.connection = mysql.connector.connect(
                host=config.datenbank.host,
                port=config.datenbank.port,
                user=config.datenbank.benutzer,
                password=config.datenbank.passwort or os.getenv('DB_PASS', ''),
                database=config.datenbank.datenbank,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci',
                autocommit=True,
                connection_timeout=60
            )
            self.cursor = self.connection.cursor(dictionary=True)
            return True
        except Error as e:
            logger.error(f"Verbindungsfehler: {e}")
            return False

    def trennen(self):
        """Trennt die Datenbankverbindung"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def sensor_speichern(self, sensor_id: str, sensor_typ: str, name: str = None) -> int:
        """Speichert einen neuen Sensor oder aktualisiert existierenden"""
        conn = _neue_verbindung()
        if not conn:
            return 0

        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                INSERT INTO sensoren (sensor_id, sensor_typ, name, aktiviert, created_at)
                VALUES (%s, %s, %s, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    sensor_typ = VALUES(sensor_typ),
                    name = COALESCE(VALUES(name), name),
                    updated_at = NOW()
            """
            cursor.execute(sql, (sensor_id, sensor_typ, name or sensor_id))
            conn.commit()

            cursor.execute("SELECT LAST_INSERT_ID() as id")
            ergebnis = cursor.fetchone()
            sensor_db_id = ergebnis['id'] if ergebnis else 0

            cursor.close()
            conn.close()
            return sensor_db_id

        except Error as e:
            logger.error(f"Fehler beim Speichern des Sensors: {e}")
            conn.rollback()
            conn.close()
            return 0

    def messung_speichern(self, sensor_id: str, wert: float, status: str) -> bool:
        """Speichert eine Sensor-Messung"""
        conn = _neue_verbindung()
        if not conn:
            return False

        try:
            cursor = conn.cursor(dictionary=True)

            # Sensor-ID holen
            cursor.execute("SELECT id FROM sensoren WHERE sensor_id = %s", (sensor_id,))
            ergebnis = cursor.fetchone()

            if not ergebnis:
                cursor.close()
                conn.close()
                return False

            sensor_db_id = ergebnis['id']

            # Messung speichern
            sql = "INSERT INTO messungen (sensor_id, wert, status, timestamp) VALUES (%s, %s, %s, NOW())"
            cursor.execute(sql, (sensor_db_id, wert, status))
            conn.commit()

            cursor.close()
            conn.close()
            return True

        except Error as e:
            logger.error(f"Fehler beim Speichern der Messung: {e}")
            conn.rollback()
            conn.close()
            return False

    def letzte_messungen_abrufen(self, sensor_id: str, limit: int = 100) -> List[Dict]:
        """Ruft die letzten Messungen eines Sensors ab"""
        conn = _neue_verbindung()
        if not conn:
            return []

        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT m.wert, m.status, m.timestamp
                FROM messungen m
                JOIN sensoren s ON m.sensor_id = s.id
                WHERE s.sensor_id = %s
                ORDER BY m.timestamp DESC
                LIMIT %s
            """
            cursor.execute(sql, (sensor_id, limit))
            ergebnis = cursor.fetchall()
            cursor.close()
            conn.close()
            return ergebnis

        except Error as e:
            logger.error(f"Fehler beim Abrufen der Messungen: {e}")
            conn.close()
            return []

    def alarm_speichern(self, sensor_id: str, alarm_typ: str, nachricht: str,
                       wert: float, schwellwert: float) -> int:
        """Speichert einen neuen Alarm"""
        conn = _neue_verbindung()
        if not conn:
            return 0

        try:
            cursor = conn.cursor(dictionary=True)

            # Sensor-ID holen
            cursor.execute("SELECT id FROM sensoren WHERE sensor_id = %s", (sensor_id,))
            ergebnis = cursor.fetchone()

            if not ergebnis:
                cursor.close()
                conn.close()
                return 0

            sensor_db_id = ergebnis['id']

            # Alarm speichern
            sql = """
                INSERT INTO alarme (sensor_id, alarm_typ, nachricht, wert, schwellwert, status, created_at)
                VALUES (%s, %s, %s, %s, %s, 'aktiv', NOW())
            """
            cursor.execute(sql, (sensor_db_id, alarm_typ, nachricht, wert, schwellwert))
            conn.commit()

            cursor.execute("SELECT LAST_INSERT_ID() as id")
            ergebnis = cursor.fetchone()
            alarm_id = ergebnis['id'] if ergebnis else 0

            cursor.close()
            conn.close()
            return alarm_id

        except Error as e:
            logger.error(f"Fehler beim Speichern des Alarms: {e}")
            conn.rollback()
            conn.close()
            return 0

    def alarm_quittieren(self, alarm_id: int) -> bool:
        """Quittiert einen Alarm"""
        conn = _neue_verbindung()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            sql = "UPDATE alarme SET status = 'quittiert', quittiert_at = NOW() WHERE id = %s"
            cursor.execute(sql, (alarm_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True

        except Error as e:
            logger.error(f"Fehler beim Quittieren des Alarms: {e}")
            conn.rollback()
            conn.close()
            return False

    def aktive_alarme_abrufen(self) -> List[Dict]:
        """Ruft alle aktiven Alarme ab"""
        conn = _neue_verbindung()
        if not conn:
            return []

        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT a.id, a.alarm_typ, a.nachricht, a.wert, a.schwellwert,
                       a.created_at, s.sensor_id
                FROM alarme a
                JOIN sensoren s ON a.sensor_id = s.id
                WHERE a.status = 'aktiv'
                ORDER BY a.created_at DESC
            """
            cursor.execute(sql)
            ergebnis = cursor.fetchall()
            cursor.close()
            conn.close()
            return ergebnis

        except Error as e:
            logger.error(f"Fehler beim Abrufen der Alarme: {e}")
            conn.close()
            return []

    def alle_alarme_abrufen(self, limit: int = 100) -> List[Dict]:
        """Ruft alle Alarme (Historie) ab"""
        conn = _neue_verbindung()
        if not conn:
            return []

        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT a.id, a.alarm_typ, a.nachricht, a.wert, a.schwellwert,
                       a.status, a.created_at, a.quittiert_at, s.sensor_id
                FROM alarme a
                JOIN sensoren s ON a.sensor_id = s.id
                ORDER BY a.created_at DESC
                LIMIT %s
            """
            cursor.execute(sql, (limit,))
            ergebnis = cursor.fetchall()
            cursor.close()
            conn.close()
            return ergebnis

        except Error as e:
            logger.error(f"Fehler beim Abrufen der Alarm-Historie: {e}")
            conn.close()
            return []

    def statistik_abrufen(self, sensor_id: str, stunden: int = 24) -> Dict:
        """Ruft Statistiken für einen Sensor ab"""
        conn = _neue_verbindung()
        if not conn:
            return {'min': 0, 'max': 0, 'durchschnitt': 0, 'anzahl': 0}

        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT
                    MIN(m.wert) as min_wert,
                    MAX(m.wert) as max_wert,
                    AVG(m.wert) as durchschnitt,
                    COUNT(*) as anzahl
                FROM messungen m
                JOIN sensoren s ON m.sensor_id = s.id
                WHERE s.sensor_id = %s
                  AND m.timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
            """
            cursor.execute(sql, (sensor_id, stunden))
            ergebnis = cursor.fetchone()

            cursor.close()
            conn.close()

            return {
                'min': float(ergebnis['min_wert']) if ergebnis and ergebnis['min_wert'] else 0,
                'max': float(ergebnis['max_wert']) if ergebnis and ergebnis['max_wert'] else 0,
                'durchschnitt': float(ergebnis['durchschnitt']) if ergebnis and ergebnis['durchschnitt'] else 0,
                'anzahl': int(ergebnis['anzahl']) if ergebnis and ergebnis['anzahl'] else 0
            }

        except Error as e:
            logger.error(f"Fehler beim Abrufen der Statistik: {e}")
            conn.close()
            return {'min': 0, 'max': 0, 'durchschnitt': 0, 'anzahl': 0}

    def alle_sensoren_abrufen(self) -> List[Dict]:
        """Ruft alle Sensoren ab"""
        conn = _neue_verbindung()
        if not conn:
            return []

        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT s.id, s.sensor_id, s.sensor_typ, s.name, s.aktiviert,
                       s.created_at, s.updated_at,
                       (SELECT m.wert FROM messungen m WHERE m.sensor_id = s.id ORDER BY m.timestamp DESC LIMIT 1) as letzter_wert,
                       (SELECT m.timestamp FROM messungen m WHERE m.sensor_id = s.id ORDER BY m.timestamp DESC LIMIT 1) as letzter_zeitpunkt
                FROM sensoren s
                WHERE s.aktiviert = 1
                ORDER BY s.name
            """
            cursor.execute(sql)
            ergebnis = cursor.fetchall()
            cursor.close()
            conn.close()
            return ergebnis

        except Error as e:
            logger.error(f"Fehler beim Abrufen der Sensoren: {e}")
            conn.close()
            return []


# Globale Datenbank-Instanz
datenbank = Datenbank()
