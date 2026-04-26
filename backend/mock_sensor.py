"""
Mock-Sensor für lokale Tests
============================

Sendet fiktive Sensordaten direkt an die MariaDB Datenbank
(kein MQTT Broker nötig).

Verwendung:
    python mock_sensor.py

Daten werden alle 10 Sekunden generiert und in die DB geschrieben.
Für IHK-Dokumentation: Zeigt ein funktionierendes System.

Sensoren (passend zum DB-Schema):
- DS18B20 (Temperatur): GPIO 4
- SHT31 (Temperatur + Feuchtigkeit): I2C
- MQ-2 (Rauchgas): GPIO 1
- PIR (Bewegung): GPIO 21

@author Marc-Dennis Haberland
@date 17.04.2026
Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
"""

import random
import time
import logging
from datetime import datetime
import mysql.connector
from mysql.connector import Error

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# DB Konfiguration (identisch zum Backend)
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'backend_user',
    'password': 'backend123',
    'database': 'serverraum_ueberwachung'
}

# Sensoren die simuliert werden
# Format: (sensor_id, name, typ, einheit, min_wert, max_wert)
SENSOREN = [
    ('ds18b20_01', 'DS18B20 Temperatursensor', 'ds18b20', '°C', 21.0, 26.0),
    ('sht31_temp_01', 'SHT31 Temperatursensor', 'sht31', '°C', 21.5, 26.5),
    ('sht31_feuchte_01', 'SHT31 Feuchtigkeitssensor', 'sht31', '%', 42.0, 58.0),
    ('mq2_01', 'MQ-2 Rauchgassensor', 'mq2', 'ppm', 80, 150),
    ('pir_01', 'PIR Bewegungsmelder', 'pir', '', 0, 1),
]


def verbinde_db():
    """Verbindet zur MariaDB"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        logger.info("MariaDB verbunden")
        return conn
    except Error as e:
        logger.error(f"DB-Verbindungsfehler: {e}")
        return None


def sensoren_initialisieren(conn):
    """Erstellt oder aktualisiert Sensoren in der DB"""
    cursor = conn.cursor()
    
    for sensor_id, name, typ, einheit, _, _ in SENSOREN:
        try:
            # Prüfe ob Sensor existiert
            cursor.execute(
                "SELECT id FROM sensoren WHERE sensor_id = %s",
                (sensor_id,)
            )
            result = cursor.fetchone()
            
            if result:
                # Update vorhanden
                cursor.execute("""
                    UPDATE sensoren 
                    SET name = %s, sensor_typ = %s, einheit = %s, aktiv = 1
                    WHERE sensor_id = %s
                """, (name, typ, einheit, sensor_id))
                logger.info(f"Sensor aktualisiert: {sensor_id}")
            else:
                # Neu einfügen
                cursor.execute("""
                    INSERT INTO sensoren (sensor_id, sensor_typ, name, einheit, aktiv)
                    VALUES (%s, %s, %s, %s, 1)
                """, (sensor_id, typ, name, einheit))
                logger.info(f"Sensor erstellt: {sensor_id}")
                
        except Error as e:
            logger.error(f"Fehler bei Sensor {sensor_id}: {e}")
    
    conn.commit()
    cursor.close()


def generate_sensor_value(sensor_id, min_val, max_val, typ, einheit):
    """
    Generiert realistischen Sensorwert
    
    @param sensor_id: ID des Sensors
    @param min_val: Minimalwert
    @param max_val: Maximalwert
    @param typ: Sensortyp
    @param einheit: Einheit des Sensors
    @return: Tuple (wert, status)
    """
    if typ == 'pir':
        # PIR: 20% Wahrscheinlichkeit für Bewegung
        wert = 1.0 if random.random() < 0.2 else 0.0
        status = "BEWEGUNG!" if wert == 1.0 else "OK"
    elif typ == 'ds18b20':
        # Temperatur: langsame Änderungen
        wert = round(random.uniform(min_val, max_val), 1)
        # Gelegentlich ein Alarm-Wert
        if random.random() < 0.05:
            wert = round(random.uniform(28.0, 31.0), 1)
            status = "WARNUNG"
        else:
            status = "OK"
    elif typ == 'sht31' and einheit == '%':
        # Feuchtigkeit
        wert = round(random.uniform(min_val, max_val), 1)
        status = "OK"
        if wert > 65 or wert < 40:
            status = "WARNUNG"
    elif typ == 'sht31':
        # Temperatur
        wert = round(random.uniform(min_val, max_val), 1)
        status = "OK"
        if wert > 28 or wert < 18:
            status = "WARNUNG"
    elif typ == 'mq2':
        # Rauchgas
        wert = random.randint(int(min_val), int(max_val))
        status = "OK"
        if wert > 180:
            status = "ALARM!"
        elif wert > 150:
            status = "WARNUNG"
    else:
        wert = round(random.uniform(min_val, max_val), 1)
        status = "OK"
    
    return wert, status


def messung_speichern(conn, sensor_id, wert, status):
    """Speichert eine Messung in die DB"""
    try:
        cursor = conn.cursor()
        
        # Hole DB-ID für sensor_id
        cursor.execute("SELECT id FROM sensoren WHERE sensor_id = %s", (sensor_id,))
        result = cursor.fetchone()
        
        if not result:
            logger.warning(f"Sensor nicht gefunden: {sensor_id}")
            return False
        
        db_id = result[0]
        
        # Messung speichern
        cursor.execute("""
            INSERT INTO messungen (sensor_id, wert, status, timestamp)
            VALUES (%s, %s, %s, NOW())
        """, (db_id, wert, status))
        
        conn.commit()
        cursor.close()
        return True
        
    except Error as e:
        logger.error(f"Fehler beim Speichern: {e}")
        return False


def main():
    """Hauptschleife"""
    logger.info("=" * 50)
    logger.info("Mock-Sensor gestartet")
    logger.info("=" * 50)
    
    # Verbinden
    conn = verbinde_db()
    if not conn:
        logger.error("Konnte nicht zur DB verbinden!")
        return
    
    # Sensoren initialisieren
    sensoren_initialisieren(conn)
    
    logger.info("")
    logger.info("Starte Messschleife... (Strg+C zum Beenden)")
    logger.info("")
    
    try:
        while True:
            # Für jeden Sensor eine Messung generieren und speichern
            for sensor_id, name, typ, einheit, min_val, max_val in SENSOREN:
                wert, status = generate_sensor_value(sensor_id, min_val, max_val, typ, einheit)
                
                if messung_speichern(conn, sensor_id, wert, status):
                    einheit_anzeige = einheit if einheit else ""
                    logger.info(
                        f"  {sensor_id:20s} = {wert:8.1f}{einheit_anzeige:4s} [{status}]"
                    )
                else:
                    logger.error(f"  Fehler bei {sensor_id}")
            
            logger.info("-" * 50)
            
            # 10 Sekunden warten
            time.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("")
        logger.info("Mock-Sensor wird beendet...")
    finally:
        if conn and conn.is_connected():
            conn.close()
            logger.info("DB-Verbindung geschlossen")


if __name__ == "__main__":
    main()
