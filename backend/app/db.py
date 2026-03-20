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
from mysql.connector import Error, pooling
from .config import config

# Logger konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connection Pool Konfiguration
POOL_NAME = "serverraum_pool"
POOL_SIZE = 5

# Globaler Connection Pool
_pool = None


def _get_pool():
    """Gibt den Connection Pool zurück (Lazy Initialization)"""
    global _pool
    if _pool is None:
        import os
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name=POOL_NAME,
                pool_size=POOL_SIZE,
                pool_reset_session=True,
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
            logger.info(f"Connection Pool '{POOL_NAME}' mit Größe {POOL_SIZE} initialisiert")
        except Error as e:
            logger.error(f"Fehler beim Erstellen des Connection Pools: {e}")
            raise
    return _pool


def _neue_verbindung():
    """Erstellt eine neue Datenbankverbindung (aus Pool)"""
    try:
        pool = _get_pool()
        conn = pool.get_connection()
        return conn
    except Error as e:
        logger.error(f"Verbindungsfehler: {e}")
        return None


class Datenbank:
    """
    Klasse für MariaDB Datenbank-Operationen
    Verwendet Connection Pooling für effiziente Verbindungsverwaltung.
    """

    def __init__(self):
        self.connection = None
        self.cursor = None

    def verbinden(self):
        """Verbindet zur Datenbank (für Kompatibilität mit main.py)"""
        import os
        try:
            pool = _get_pool()
            self.connection = pool.get_connection()
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
            self.cursor = None

    def get_pool_status(self) -> Dict:
        """Gibt Pool-Statistiken zurück"""
        try:
            pool = _get_pool()
            return {
                'pool_name': POOL_NAME,
                'pool_size': POOL_SIZE,
                'pool_available': pool.pool_size,
                'status': 'aktiv'
            }
        except Error as e:
            logger.error(f"Fehler beim Abrufen des Pool-Status: {e}")
            return {'status': 'fehler', 'fehler': str(e)}

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
            return sensor_db_id

        except Error as e:
            logger.error(f"Fehler beim Speichern des Sensors: {e}")
            conn.rollback()
            return 0

        finally:
            if conn and conn.is_connected():
                conn.close()

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
                return False

            sensor_db_id = ergebnis['id']

            # Messung speichern
            sql = "INSERT INTO messungen (sensor_id, wert, status, timestamp) VALUES (%s, %s, %s, NOW())"
            cursor.execute(sql, (sensor_db_id, wert, status))
            conn.commit()

            cursor.close()
            return True

        except Error as e:
            logger.error(f"Fehler beim Speichern der Messung: {e}")
            conn.rollback()
            return False

        finally:
            if conn and conn.is_connected():
                conn.close()

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
            return ergebnis

        except Error as e:
            logger.error(f"Fehler beim Abrufen der Messungen: {e}")
            return []

        finally:
            if conn and conn.is_connected():
                conn.close()

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
            return alarm_id

        except Error as e:
            logger.error(f"Fehler beim Speichern des Alarms: {e}")
            conn.rollback()
            return 0

        finally:
            if conn and conn.is_connected():
                conn.close()

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
            return True

        except Error as e:
            logger.error(f"Fehler beim Quittieren des Alarms: {e}")
            conn.rollback()
            return False

        finally:
            if conn and conn.is_connected():
                conn.close()

    def aktive_alarme_abrufen(self) -> List[Dict]:
        """Ruft alle aktiven Alarme ab"""
        conn = _neue_verbindung()
        if not conn:
            return []

        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT a.id, a.alarm_typ, a.nachricht, a.wert, a.schwellwert,
                       a.status, a.created_at, s.sensor_id
                FROM alarme a
                JOIN sensoren s ON a.sensor_id = s.id
                WHERE a.status = 'aktiv'
                ORDER BY a.created_at DESC
            """
            cursor.execute(sql)
            ergebnis = cursor.fetchall()
            cursor.close()
            return ergebnis

        except Error as e:
            logger.error(f"Fehler beim Abrufen der Alarme: {e}")
            return []

        finally:
            if conn and conn.is_connected():
                conn.close()

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
            return ergebnis

        except Error as e:
            logger.error(f"Fehler beim Abrufen der Alarm-Historie: {e}")
            return []

        finally:
            if conn and conn.is_connected():
                conn.close()

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

            return {
                'min': float(ergebnis['min_wert']) if ergebnis and ergebnis['min_wert'] else 0,
                'max': float(ergebnis['max_wert']) if ergebnis and ergebnis['max_wert'] else 0,
                'durchschnitt': float(ergebnis['durchschnitt']) if ergebnis and ergebnis['durchschnitt'] else 0,
                'anzahl': int(ergebnis['anzahl']) if ergebnis and ergebnis['anzahl'] else 0
            }

        except Error as e:
            logger.error(f"Fehler beim Abrufen der Statistik: {e}")
            return {'min': 0, 'max': 0, 'durchschnitt': 0, 'anzahl': 0}

        finally:
            if conn and conn.is_connected():
                conn.close()

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
            return ergebnis

        except Error as e:
            logger.error(f"Fehler beim Abrufen der Sensoren: {e}")
            return []

        finally:
            if conn and conn.is_connected():
                conn.close()

    def schwellwerte_abrufen(self) -> Dict:
        """Ruft alle Schwellwerte aus alarm_konfiguration ab"""
        conn = _neue_verbindung()
        if not conn:
            return {}

        try:
            cursor = conn.cursor(dictionary=True)
            sql = "SELECT sensor_id, alarm_typ, wert FROM alarm_konfiguration"
            cursor.execute(sql)
            ergebnis = cursor.fetchall()
            cursor.close()

            # Umwandeln in Dict mit sensor_id als Key
            schwellwerte = {}
            for row in ergebnis:
                key = f"{row['sensor_id']}_{row['alarm_typ']}"
                schwellwerte[key] = row['wert']

            return schwellwerte

        except Error as e:
            logger.error(f"Fehler beim Abrufen der Schwellwerte: {e}")
            return {}

        finally:
            if conn and conn.is_connected():
                conn.close()


# Globale Datenbank-Instanz
datenbank = Datenbank()
