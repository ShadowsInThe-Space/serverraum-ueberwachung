"""
Datenbank-Modul für MariaDB
==========================

@author Marc-Dennis Haberland
@date 04.03.2026
"""

import logging
from typing import List, Dict

from mysql.connector import Error, pooling

from .config import config

logger = logging.getLogger(__name__)

POOL_NAME = "serverraum_pool"
POOL_SIZE = 5
_pool = None


def _get_pool():
    """Connection Pool (Lazy Init)"""
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name=POOL_NAME,
            pool_size=POOL_SIZE,
            host=config.datenbank.host,
            port=config.datenbank.port,
            user=config.datenbank.benutzer,
            password=config.datenbank.passwort,
            database=config.datenbank.datenbank,
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
            autocommit=True,
            connection_timeout=60,
        )
    return _pool


def _query(sql: str, params: tuple = ()) -> List[Dict]:
    """Führt Query aus und gibt Ergebnis zurück"""
    conn = None
    try:
        conn = _get_pool().get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params)
        result = cursor.fetchall()
        cursor.close()
        return result
    except Error as e:
        logger.error(f"Query Fehler: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            conn.close()


def _execute(sql: str, params: tuple = (), commit: bool = True) -> bool:
    """Führt INSERT/UPDATE/DELETE aus"""
    conn = None
    try:
        conn = _get_pool().get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        if commit:
            conn.commit()
        cursor.close()
        return True
    except Error as e:
        logger.error(f"Execute Fehler: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()


class Datenbank:
    """Datenbank-Operationen"""

    def __init__(self):
        self.connection = None
        self.cursor = None

    def verbinden(self) -> bool:
        try:
            pool = _get_pool()
            self.connection = pool.get_connection()
            self.cursor = self.connection.cursor(dictionary=True)
            return True
        except Error as e:
            logger.error(f"Verbindungsfehler: {e}")
            return False

    def trennen(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None

    def sensor_speichern(self, sensor_id: str, sensor_typ: str, name: str = None, gpio_pin: int = None, beschreibung: str = None) -> int:
        sql = """
            INSERT INTO sensoren (sensor_id, sensor_typ, name, gpio_pin, beschreibung, aktiv, created_at)
            VALUES (%s, %s, %s, %s, %s, 1, NOW())
            ON DUPLICATE KEY UPDATE
                sensor_typ = VALUES(sensor_typ),
                name = VALUES(name),
                gpio_pin = VALUES(gpio_pin),
                beschreibung = VALUES(beschreibung),
                updated_at = NOW()
        """
        if _execute(sql, (sensor_id, sensor_typ, name or sensor_id, gpio_pin, beschreibung)):
            result = _query("SELECT id FROM sensoren WHERE sensor_id = %s", (sensor_id,))
            return result[0]["id"] if result else 0
        return 0

    def alle_sensoren_abrufen(self) -> List[Dict]:
        """Alle Sensoren abrufen - mit gpio_pin und beschreibung"""
        return _query("SELECT id, sensor_id, sensor_typ, name, gpio_pin, beschreibung, aktiv FROM sensoren ORDER BY created_at DESC")

    def messung_speichern(self, sensor_id: str, wert: float, status: str, einheit: str = None) -> bool:
        result = _query("SELECT id FROM sensoren WHERE sensor_id = %s", (sensor_id,))
        if not result:
            return False
        sensor_db_id = result[0]["id"]
        return _execute(
            "INSERT INTO messungen (sensor_id, wert, einheit, status, timestamp) VALUES (%s, %s, %s, %s, NOW())",
            (sensor_db_id, wert, einheit, status),
        )

    def letzte_messungen_abrufen(self, sensor_id: str, limit: int = 100) -> List[Dict]:
        """Letzte N Messungen für Sensor - mit einheit"""
        return _query(
            """SELECT m.wert, m.einheit, m.timestamp FROM messungen m
               JOIN sensoren s ON m.sensor_id = s.id
               WHERE s.sensor_id = %s
               ORDER BY m.timestamp DESC LIMIT %s""",
            (sensor_id, limit),
        )

    def alarm_speichern(self, sensor_id: str, alarm_typ: str, nachricht: str,
                         wert: float, schwellwert: float) -> int:
        result = _query("SELECT id FROM sensoren WHERE sensor_id = %s", (sensor_id,))
        if not result:
            return 0
        sensor_db_id = result[0]["id"]
        sql = """
            INSERT INTO alarme (sensor_id, alarm_typ, nachricht, wert, schwellwert, status, created_at)
            VALUES (%s, %s, %s, %s, %s, 'aktiv', NOW())
        """
        if _execute(sql, (sensor_db_id, alarm_typ, nachricht, wert, schwellwert)):
            result = _query("SELECT LAST_INSERT_ID() as id")
            return result[0]["id"] if result else 0
        return 0

    def alarm_quittieren(self, alarm_id: int) -> bool:
        return _execute(
            "UPDATE alarme SET status = 'quittiert', quittiert_at = NOW() WHERE id = %s",
            (alarm_id,),
        )

    def alarm_loeschen(self, alarm_id: int) -> bool:
        """Löscht einen Alarm vollständig aus der DB"""
        return _execute("DELETE FROM alarme WHERE id = %s", (alarm_id,))

    def aktive_alarme_abrufen(self) -> List[Dict]:
        return _query("""
            SELECT a.*, s.sensor_id
            FROM alarme a JOIN sensoren s ON a.sensor_id = s.id
            WHERE a.status = 'aktiv' ORDER BY a.created_at DESC
        """)

    def alle_alarme_abrufen(self, limit: int = 100) -> List[Dict]:
        return _query("""
            SELECT a.*, s.sensor_id
            FROM alarme a JOIN sensoren s ON a.sensor_id = s.id
            ORDER BY a.created_at DESC LIMIT %s
        """, (limit,))

    # =============================================================================
    # ALARM EMAILS
    # =============================================================================

    def alarm_email_speichern(self, alarm_id: int, empfaenger: str, subject: str,
                              body: str = None, sende_status: str = 'ausstehend',
                              error_message: str = None) -> int:
        """Speichert ein gesendetes Alarm-Email"""
        sql = """
            INSERT INTO alarm_emails (alarm_id, empfaenger, subject, body, sende_status, error_message, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        if _execute(sql, (alarm_id, empfaenger, subject, body, sende_status, error_message)):
            result = _query("SELECT LAST_INSERT_ID() as id")
            return result[0]["id"] if result else 0
        return 0

    def alarm_email_aktualisieren(self, email_id: int, sende_status: str,
                                   error_message: str = None) -> bool:
        """Aktualisiert den Status einer gesendeten Email"""
        sql = """
            UPDATE alarm_emails
            SET sende_status = %s, error_message = %s
            WHERE id = %s
        """
        return _execute(sql, (sende_status, error_message, email_id))

    def alle_alarm_emails_abrufen(self, limit: int = 100) -> List[Dict]:
        """Alle gesendeten Alarm-Emails abrufen"""
        return _query("""
            SELECT ae.*, a.alarm_typ, a.nachricht, a.wert, a.schwellwert,
                   a.created_at as alarm_zeitstempel, s.sensor_id
            FROM alarm_emails ae
            JOIN alarme a ON ae.alarm_id = a.id
            JOIN sensoren s ON a.sensor_id = s.id
            ORDER BY ae.created_at DESC
            LIMIT %s
        """, (limit,))

    def alarm_email_antwort_speichern(self, email_id: int, empfaenger_email: str,
                                       antwort_text: str = None) -> int:
        """Speichert eine Antwort auf eine Alarm-Email"""
        sql = """
            INSERT INTO alarm_email_antworten (alarm_email_id, empfaenger_email, antwort_text, antwort_zeitpunkt)
            VALUES (%s, %s, %s, NOW())
        """
        if _execute(sql, (email_id, empfaenger_email, antwort_text)):
            result = _query("SELECT LAST_INSERT_ID() as id")
            return result[0]["id"] if result else 0
        return 0

    def alarm_email_antworten_abrufen(self, email_id: int) -> List[Dict]:
        """Alle Antworten auf eine bestimmte Alarm-Email abrufen"""
        return _query("""
            SELECT * FROM alarm_email_antworten
            WHERE alarm_email_id = %s
            ORDER BY antwort_zeitpunkt DESC
        """, (email_id,))

    def statistik_abrufen(self, sensor_id: str, stunden: int = 24) -> Dict:
        result = _query("""
            SELECT MIN(m.wert) as min, MAX(m.wert) as max,
                   AVG(m.wert) as durchschnitt, COUNT(*) as anzahl,
                   m.einheit
            FROM messungen m JOIN sensoren s ON m.sensor_id = s.id
            WHERE s.sensor_id = %s AND m.timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
        """, (sensor_id, stunden))

        if result and result[0]["min"] is not None:
            r = result[0]
            return {
                "min": float(r["min"]),
                "max": float(r["max"]),
                "durchschnitt": float(r["durchschnitt"]),
                "anzahl": int(r["anzahl"]),
                "einheit": r.get("einheit"),
            }
        return {"min": 0, "max": 0, "durchschnitt": 0, "anzahl": 0, "einheit": None}

    # =============================================================================
    # ALARM KONFIGURATION
    # =============================================================================

    def alarm_konfiguration_abrufen(self, sensor_id: str) -> Dict:
        """Alarm-Konfiguration für einen Sensor abrufen"""
        result = _query("""
            SELECT a.*, s.sensor_id
            FROM alarm_konfiguration a
            JOIN sensoren s ON a.sensor_id = s.id
            WHERE s.sensor_id = %s
        """, (sensor_id,))
        return result[0] if result else None

    def alle_alarm_konfigurationen_abrufen(self) -> List[Dict]:
        """Alle Alarm-Konfigurationen abrufen"""
        return _query("""
            SELECT a.*, s.sensor_id, s.name as sensor_name
            FROM alarm_konfiguration a
            JOIN sensoren s ON a.sensor_id = s.id
        """)

    def alarm_konfiguration_speichern(
        self,
        sensor_id: str,
        alarm_typ: str,
        schwellwert_min: float = None,
        schwellwert_max: float = None,
        alarmierung_email: bool = False,
        alarmierung_led: bool = False,
        alarmierung_buzzer: bool = False,
        alarmierung_dashboard: bool = True
    ) -> bool:
        """Alarm-Konfiguration speichern oder aktualisieren"""
        result = _query("SELECT id FROM sensoren WHERE sensor_id = %s", (sensor_id,))
        if not result:
            return False
        sensor_db_id = result[0]["id"]

        sql = """
            INSERT INTO alarm_konfiguration
                (sensor_id, alarm_typ, schwellwert_min, schwellwert_max,
                 alarmierung_email, alarmierung_led, alarmierung_buzzer, alarmierung_dashboard,
                 created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
                alarm_typ = VALUES(alarm_typ),
                schwellwert_min = VALUES(schwellwert_min),
                schwellwert_max = VALUES(schwellwert_max),
                alarmierung_email = VALUES(alarmierung_email),
                alarmierung_led = VALUES(alarmierung_led),
                alarmierung_buzzer = VALUES(alarmierung_buzzer),
                alarmierung_dashboard = VALUES(alarmierung_dashboard),
                updated_at = NOW()
        """
        return _execute(sql, (
            sensor_db_id, alarm_typ, schwellwert_min, schwellwert_max,
            alarmierung_email, alarmierung_led, alarmierung_buzzer, alarmierung_dashboard
        ))

    # =============================================================================
    # SYSTEM KONFIGURATION
    # =============================================================================

    def system_konfiguration_abrufen(self, schluessel: str) -> Dict:
        """System-Konfiguration für einen Schlüssel abrufen"""
        result = _query("""
            SELECT * FROM system_konfiguration
            WHERE konfiguration_schluessel = %s
        """, (schluessel,))
        return result[0] if result else None

    def alle_system_konfiguration_abrufen(self) -> List[Dict]:
        """Alle System-Konfigurationen abrufen"""
        return _query("SELECT * FROM system_konfiguration ORDER BY konfiguration_schluessel")

    def system_konfiguration_speichern(self, schluessel: str, wert: str, beschreibung: str = None) -> bool:
        """System-Konfiguration speichern oder aktualisieren"""
        sql = """
            INSERT INTO system_konfiguration
                (konfiguration_schluessel, wert, beschreibung, created_at, updated_at)
            VALUES (%s, %s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
                wert = VALUES(wert),
                beschreibung = VALUES(beschreibung),
                updated_at = NOW()
        """
        return _execute(sql, (schluessel, wert, beschreibung))


datenbank = Datenbank()
