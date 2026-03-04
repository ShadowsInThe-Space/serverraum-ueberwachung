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


class Datenbank:
    """
    Klasse für MariaDB Datenbank-Operationen
    """

    def __init__(self):
        """Initialisiert die Datenbank-Verbindung"""
        self.connection = None
        self.cursor = None

    def verbinden(self) -> bool:
        """
        Verbindet mit der MariaDB Datenbank

        @return True wenn Verbindung erfolgreich, False bei Fehler
        """
        try:
            self.connection = mysql.connector.connect(
                host=config.datenbank.host,
                port=config.datenbank.port,
                user=config.datenbank.benutzer,
                password=config.datenbank.passwort,
                database=config.datenbank.datenbank,
                autocommit=False  # Transactions manuell steuern
            )

            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                logger.info(f"MariaDB verbunden: {config.datenbank.host}/{config.datenbank.datenbank}")
                return True

        except Error as e:
            logger.error(f"Datenbank-Verbindungsfehler: {e}")

        return False

    def trennen(self):
        """Trennt die Datenbank-Verbindung"""
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Datenbank getrennt")

    # -------------------------------------------------------------------------
    # Sensor-Operationen
    # -------------------------------------------------------------------------

    def sensor_speichern(self, sensor_id: str, sensor_typ: str, name: str = None) -> int:
        """
        Speichert einen neuen Sensor oder aktualisiert existierenden

        @param sensor_id Eindeutige Sensor-ID (aus ESP32)
        @param sensor_typ Typ des Sensors (DHT22, MQ2, etc.)
        @param name Anzeigename (optional)
        @return Sensor-ID in Datenbank
        """
        sql = """
            INSERT INTO sensoren (sensor_id, sensor_typ, name, aktiviert, created_at)
            VALUES (%s, %s, %s, 1, NOW())
            ON DUPLICATE KEY UPDATE
                sensor_typ = VALUES(sensor_typ),
                name = COALESCE(VALUES(name), name),
                updated_at = NOW()
        """

        try:
            self.cursor.execute(sql, (sensor_id, sensor_typ, name or sensor_id))
            self.connection.commit()

            # ID zurückgeben (bei INSERT die neue, bei UPDATE die existierende)
            self.cursor.execute("SELECT LAST_INSERT_ID() as id")
            ergebnis = self.cursor.fetchone()
            return ergebnis['id'] if ergebnis else 0

        except Error as e:
            logger.error(f"Fehler beim Speichern des Sensors: {e}")
            self.connection.rollback()
            return 0

    def messung_speichern(self, sensor_id: str, wert: float, status: str) -> bool:
        """
        Speichert eine Sensor-Messung

        @param sensor_id Eindeutige Sensor-ID
        @param wert Gemessener Wert
        @param status Sensor-Status (OK, FEHLER, etc.)
        @return True wenn erfolgreich
        """
        # Zuerst Sensor-ID aus Datenbank holen
        self.cursor.execute("SELECT id FROM sensoren WHERE sensor_id = %s", (sensor_id,))
        ergebnis = self.cursor.fetchone()

        if not ergebnis:
            logger.warning(f"Sensor nicht gefunden: {sensor_id}")
            return False

        sensor_db_id = ergebnis['id']

        sql = """
            INSERT INTO messungen (sensor_id, wert, status, timestamp)
            VALUES (%s, %s, %s, NOW())
        """

        try:
            self.cursor.execute(sql, (sensor_db_id, wert, status))
            self.connection.commit()
            return True

        except Error as e:
            logger.error(f"Fehler beim Speichern der Messung: {e}")
            self.connection.rollback()
            return False

    def letzte_messungen_abrufen(self, sensor_id: str, limit: int = 100) -> List[Dict]:
        """
        Ruft die letzten Messungen eines Sensors ab

        @param sensor_id Sensor-ID
        @param limit Anzahl der Messungen
        @return Liste von Messungen
        """
        sql = """
            SELECT m.wert, m.status, m.timestamp
            FROM messungen m
            JOIN sensoren s ON m.sensor_id = s.id
            WHERE s.sensor_id = %s
            ORDER BY m.timestamp DESC
            LIMIT %s
        """

        try:
            self.cursor.execute(sql, (sensor_id, limit))
            return self.cursor.fetchall()

        except Error as e:
            logger.error(f"Fehler beim Abrufen der Messungen: {e}")
            return []

    # -------------------------------------------------------------------------
    # Alarm-Operationen
    # -------------------------------------------------------------------------

    def alarm_speichern(self, sensor_id: str, alarm_typ: str, nachricht: str,
                       wert: float, schwellwert: float) -> int:
        """
        Speichert einen neuen Alarm

        @param sensor_id Sensor-ID
        @param alarm_typ Typ des Alarms (TEMPERATUR_HOCH, RAUCHGAS, etc.)
        @param nachricht Beschreibung des Alarms
        @param wert Aktueller Messwert
        @param schwellwert Überschrittener Schwellwert
        @return Alarm-ID
        """
        # Sensor-ID holen
        self.cursor.execute("SELECT id FROM sensoren WHERE sensor_id = %s", (sensor_id,))
        ergebnis = self.cursor.fetchone()

        if not ergebnis:
            logger.warning(f"Sensor nicht gefunden für Alarm: {sensor_id}")
            return 0

        sensor_db_id = ergebnis['id']

        sql = """
            INSERT INTO alarme (sensor_id, alarm_typ, nachricht, wert, schwellwert, status, created_at)
            VALUES (%s, %s, %s, %s, %s, 'aktiv', NOW())
        """

        try:
            self.cursor.execute(sql, (sensor_db_id, alarm_typ, nachricht, wert, schwellwert))
            self.connection.commit()

            self.cursor.execute("SELECT LAST_INSERT_ID() as id")
            ergebnis = self.cursor.fetchone()
            return ergebnis['id'] if ergebnis else 0

        except Error as e:
            logger.error(f"Fehler beim Speichern des Alarms: {e}")
            self.connection.rollback()
            return 0

    def alarm_quittieren(self, alarm_id: int) -> bool:
        """
        Quittiert einen Alarm (Benutzer hat ihn gesehen)

        @param alarm_id Alarm-ID
        @return True wenn erfolgreich
        """
        sql = """
            UPDATE alarme
            SET status = 'quittiert', quittiert_at = NOW()
            WHERE id = %s
        """

        try:
            self.cursor.execute(sql, (alarm_id,))
            self.connection.commit()
            return True

        except Error as e:
            logger.error(f"Fehler beim Quittieren des Alarms: {e}")
            self.connection.rollback()
            return False

    def aktive_alarme_abrufen(self) -> List[Dict]:
        """
        Ruft alle aktiven (nicht-quittierten) Alarme ab

        @return Liste aktiver Alarme
        """
        sql = """
            SELECT a.id, a.alarm_typ, a.nachricht, a.wert, a.schwellwert,
                   a.created_at, s.sensor_id
            FROM alarme a
            JOIN sensoren s ON a.sensor_id = s.id
            WHERE a.status = 'aktiv'
            ORDER BY a.created_at DESC
        """

        try:
            self.cursor.execute(sql)
            return self.cursor.fetchall()

        except Error as e:
            logger.error(f"Fehler beim Abrufen der Alarme: {e}")
            return []

    def alle_alarme_abrufen(self, limit: int = 100) -> List[Dict]:
        """
        Ruft alle Alarme (Historie) ab

        @return Liste aller Alarme
        """
        sql = """
            SELECT a.id, a.alarm_typ, a.nachricht, a.wert, a.schwellwert,
                   a.status, a.created_at, a.quittiert_at, s.sensor_id
            FROM alarme a
            JOIN sensoren s ON a.sensor_id = s.id
            ORDER BY a.created_at DESC
            LIMIT %s
        """

        try:
            self.cursor.execute(sql, (limit,))
            return self.cursor.fetchall()

        except Error as e:
            logger.error(f"Fehler beim Abrufen der Alarm-Historie: {e}")
            return []

    # -------------------------------------------------------------------------
    # Statistik
    # -------------------------------------------------------------------------

    def statistik_abrufen(self, sensor_id: str, stunden: int = 24) -> Dict:
        """
        Ruft Statistiken für einen Sensor ab

        @param sensor_id Sensor-ID
        @param stunden Zeitraum in Stunden
        @return Dictionary mit min, max, durchschnitt
        """
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

        try:
            self.cursor.execute(sql, (sensor_id, stunden))
            ergebnis = self.cursor.fetchone()

            return {
                'min': float(ergebnis['min_wert']) if ergebnis['min_wert'] else 0,
                'max': float(ergebnis['max_wert']) if ergebnis['max_wert'] else 0,
                'durchschnitt': float(ergebnis['durchschnitt']) if ergebnis['durchschnitt'] else 0,
                'anzahl': int(ergebnis['anzahl']) if ergebnis['anzahl'] else 0
            }

        except Error as e:
            logger.error(f"Fehler beim Abrufen der Statistik: {e}")
            return {'min': 0, 'max': 0, 'durchschnitt': 0, 'anzahl': 0}


# Globale Datenbank-Instanz
datenbank = Datenbank()
