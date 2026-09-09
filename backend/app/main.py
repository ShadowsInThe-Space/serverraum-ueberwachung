"""
FastAPI Backend für Serverraum-Überwachung
=========================================

Starten mit:
    uvicorn app.main:app --host 0.0.0.0 --port 8000

@author Marc-Dennis Haberland
@date 16.03.2026
"""

import logging
import os
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import config as config_module
from .mqtt_client import mqtt_client
from .db import datenbank
from .alarm_engine import alarm_engine

config = config_module.config
logger = logging.getLogger(__name__)

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")


# =============================================================================
# Response Models
# =============================================================================

@dataclass
class SensorResponse:
    """
    Response-Modell für Sensor-Daten.

    Repräsentiert einen Sensor mit seinen aktuellen Messwerten
    und Konfigurationsdaten für die API-Responses.

    Attributes:
        sensor_id:     Eindeutige Sensor-ID (z.B. "sensor_01")
        sensor_typ:   Sensortyp (z.B. "DS18B20", "MQ2")
        name:         Anzeigename des Sensors
        aktiviert:    Ob Sensor aktiv ist
        letzte_messung: Letzter Messwert
        letzte_zeit:   Zeitstempel der letzten Messung
    """
    sensor_id: str
    sensor_typ: str
    name: Optional[str] = None
    aktiviert: bool = True
    letzte_messung: Optional[float] = None
    letzte_zeit: Optional[str] = None


# =============================================================================
# Error Response
# =============================================================================

def error_response(error: str, detail: str, status_code: int) -> JSONResponse:
    """
    Erstellt eine standardisierte Fehler-Response.

    Args:
        error:      Fehler-Typ (z.B. "not_found", "internal_error")
        detail:     Detaillierte Fehlermeldung
        status_code: HTTP Status-Code

    Returns:
        JSONResponse mit strukturiertem Fehler-Objekt
    """
    return JSONResponse(
        status_code=status_code,
        content={"error": error, "detail": detail, "status_code": status_code},
    )


# =============================================================================
# Startup / Shutdown
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Backend startet...")

    datenbank.verbinden()
    mqtt_client.verbinden()
    alarm_engine.initialisiere_gpio()

    def on_sensor_data(sensor_id: str, sensor_typ: str, wert: float):
        """
        Callback-Funktion für eingehende Sensor-Daten vom MQTT-Client.
        Wird für jede neue Messung aufgerufen und prüft ob ein Alarm ausgelöst werden soll.

        Args:
            sensor_id:  eindeutige ID des Sensors (z.B. "sensor_01")
            sensor_typ: Typ des Sensors (z.B. "temperatur", "humidity")
            wert:       gemessener Wert (z.B. 25.3)
        """
        # AlarmEngine prüft ob der Wert gegen konfigurierte Schwellwerte verstößt
        alarm = alarm_engine.pruefe_alarm(sensor_id, sensor_typ, wert)
        if alarm:
            # Alarm gefunden → AlarmEngine führt Aktionen aus (LED, Buzzer, Email, Dashboard)
            alarm_engine.alarm_ausloesen(alarm)

    # Registriere Callback beim MQTT-Client
    # Bei jeder neuen MQTT-Nachricht vom Typ "data" wird this.on_sensor_data aufgerufen
    mqtt_client.set_alarm_callback(on_sensor_data)

    yield

    logger.info("Backend shutdown...")
    mqtt_client.trennen()
    datenbank.trennen()
    alarm_engine.cleanup()


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="Serverraum-Überwachung API",
    version="1.0.0",
    lifespan=lifespan,
    description="REST-API für Serverraum-Sensorüberwachung mit MQTT-Anbindung"
)

# CORS-Middleware für Frontend-Zugriff
# Erlaubt alle Origins, Methoden und Header für Entwicklung
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Exception Handler
# =============================================================================

@app.exception_handler(Exception)
async def exception_handler(request, exc):
    """
    Globaler Exception-Handler für alle unbehandelten Fehler.

    Fängt alle Exceptions ab und gibt eine standardisierte JSON-Response zurück.
    In Debug-Modus wird die originale Fehlermeldung zurückgegeben.

    Args:
        request: FastAPI Request-Objekt
        exc:      Exception die aufgetreten ist

    Returns:
        JSONResponse mit Fehlerdetails
    """
    logger.error(f"Exception: {exc}")
    return error_response(
        "internal_error", str(exc) if config.api.debug else "Interner Fehler", 500
    )


# =============================================================================
# Static Files
# =============================================================================

if os.path.exists(STATIC_DIR):
    from fastapi.staticfiles import StaticFiles
    # Statische Dateien für Frontend bereitstellen
    # /static -> Frontend Root (JS, CSS, Bilder)
    # /js     -> Direkter Zugriff auf JS-Dateien für Kompatibilität
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.mount("/js", StaticFiles(directory=os.path.join(STATIC_DIR, "js")), name="js")


# =============================================================================
# API Endpunkte
# =============================================================================

@app.get("/")
async def root():
    """
    Root-Endpoint der API.

    Gibt entweder die index.html des Frontends zurück
    oder API-Metadaten als JSON.

    Returns:
        FileResponse mit index.html oder JSON mit API-Info
    """
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        from fastapi.responses import FileResponse
        return FileResponse(index_path)
    return {"name": "Serverraum-Überwachung API", "version": "1.0.0", "status": "online"}


@app.get("/status")
async def status():
    """
    System-Status-Endpunkt.

    Gibt den aktuellen Verbindungsstatus von MQTT und Datenbank zurück
    sowie die Anzahl der aktiven Alarme.

    Returns:
        Dictionary mit Status-Informationen:
        - status: "online"
        - mqtt_verbunden: MQTT Verbindung aktiv
        - datenbank_verbunden: DB Verbindung aktiv
        - aktive_alarme: Anzahl aktiver Alarme
    """
    aktive_alarme = datenbank.aktive_alarme_abrufen()
    return {
        "status": "online",
        "mqtt_verbunden": mqtt_client.ist_verbunden,
        "datenbank_verbunden": datenbank.connection is not None,
        "aktive_alarme": len(aktive_alarme),
    }


@app.get("/sensoren")
async def sensoren_liste():
    """
    Liste aller registrierten Sensoren.

    Ruft alle Sensoren aus der Datenbank ab und fügt
    die letzte Messung für jeden Sensor hinzu.

    Returns:
        Liste von Sensor-Objekten mit:
        - sensor_id, sensor_typ, name, gpio_pin, beschreibung
        - aktiviert: boolean
        - letzte_messung, letzte_zeit, einheit

    Raises:
        HTTPException: Bei Datenbankfehler (500)
    """
    try:
        sensoren = datenbank.alle_sensoren_abrufen()
        ergebnis = []
        for s in sensoren:
            messungen = datenbank.letzte_messungen_abrufen(s["sensor_id"], 1)
            ergebnis.append({
                "sensor_id": s["sensor_id"],
                "sensor_typ": s["sensor_typ"],
                "name": s["name"],
                "gpio_pin": s.get("gpio_pin"),
                "beschreibung": s.get("beschreibung"),
                "aktiviert": bool(s["aktiv"]),
                "letzte_messung": messungen[0]["wert"] if messungen else None,
                "letzte_zeit": str(messungen[0]["timestamp"]) if messungen else None,
                "einheit": messungen[0].get("einheit") if messungen else None,
            })
        return ergebnis
    except Exception as e:
        logger.error(f"Fehler: {e}")
        raise HTTPException(status_code=500, detail="Datenbankfehler")


@app.get("/sensoren/{sensor_id}/messungen")
async def messungen(sensor_id: str, limit: int = Query(default=100, ge=1, le=1000)):
    """
    Messungen für einen spezifischen Sensor abrufen.

    Gibt die letzten N Messungen zurück (standard: 100, max: 1000).

    Args:
        sensor_id: ID des Sensors
        limit:    Anzahl der Messungen (1-1000)

    Returns:
        Liste von Messungen mit wert und timestamp
    """
    messungen = datenbank.letzte_messungen_abrufen(sensor_id, limit)
    return [{"wert": m["wert"], "timestamp": str(m["timestamp"])} for m in messungen]


@app.get("/sensoren/{sensor_id}/statistik")
async def statistik(sensor_id: str, stunden: int = Query(default=24, ge=1, le=168)):
    """
    Statistiken für einen Sensor über einen Zeitraum.

    Berechnet Min, Max, Durchschnitt und Anzahl der Messungen
    für den angegebenen Zeitraum (standard: 24 Stunden, max: 168 = 1 Woche).

    Args:
        sensor_id: ID des Sensors
        stunden:   Zeitraum in Stunden (1-168)

    Returns:
        Dictionary mit sensor_id, min, max, durchschnitt, anzahl, einheit
    """
    stat = datenbank.statistik_abrufen(sensor_id, stunden)
    return {"sensor_id": sensor_id, **stat}


@app.get("/alarme")
async def alarme(status: Optional[str] = None, limit: int = Query(default=100, ge=1, le=1000)):
    """
    Alarme abrufen mit optionalem Status-Filter.

    Gibt entweder alle Alarme oder nur aktive Alarme zurück.

    Args:
        status: Filter "aktiv" für nur aktive Alarme, sonst alle
        limit:  Maximale Anzahl (1-1000, standard: 100)

    Returns:
        Liste von Alarmen mit id, sensor_id, alarm_typ, nachricht,
        wert, schwellwert, status, created_at, quittiert_at, letzte_aktion
    """
    if status == "aktiv":
        alarme = datenbank.aktive_alarme_abrufen()
    else:
        alarme = datenbank.alle_alarme_abrufen(limit)
    return [{
        "id": a["id"],
        "sensor_id": a["sensor_id"],
        "alarm_typ": a["alarm_typ"],
        "nachricht": a["nachricht"],
        "wert": a["wert"],
        "schwellwert": a["schwellwert"],
        "status": a["status"],
        "created_at": str(a["created_at"]),
        "quittiert_at": str(a["quittiert_at"]) if a.get("quittiert_at") else None,
        "letzte_aktion": a.get("letzte_aktion"),
    } for a in alarme]


@app.post("/alarme/{alarm_id}/quittieren")
async def alarm_quittieren(alarm_id: int):
    """
    Alarm als quittiert markieren.

    Setzt den Status des Alarms auf "quittiert" und
    speichert den Zeitstempel.

    Args:
        alarm_id: ID des zu quittierenden Alarms

    Returns:
        {"status": "erfolgreich", "alarm_id": alarm_id}

    Raises:
        HTTPException: Bei Fehler (500)
    """
    if datenbank.alarm_quittieren(alarm_id):
        return {"status": "erfolgreich", "alarm_id": alarm_id}
    raise HTTPException(status_code=500, detail="Quittieren fehlgeschlagen")


@app.delete("/alarme/{alarm_id}")
async def alarm_loeschen(alarm_id: int):
    """
    Alarm vollständig aus Datenbank löschen.

    Löscht den Alarm dauerhaft aus der Datenbank.

    Args:
        alarm_id: ID des zu löschenden Alarms

    Returns:
        {"status": "erfolgreich", "alarm_id": alarm_id}

    Raises:
        HTTPException: Bei Fehler (500)
    """
    if datenbank.alarm_loeschen(alarm_id):
        return {"status": "erfolgreich", "alarm_id": alarm_id}
    raise HTTPException(status_code=500, detail="Löschen fehlgeschlagen")


@app.post("/alarme/{alarm_id}/email")
async def alarm_email_senden(alarm_id: int):
    """
    Erinnerungs-Email für einen Alarm senden.

    Ruft den Alarm aus der Datenbank, erstellt ein Alarm-Objekt
    und leitet es an den EmailNotifier weiter.

    Args:
        alarm_id: ID des Alarms

    Returns:
        {"status": "erfolgreich", "alarm_id": alarm_id, "hinweis": "Email wurde gespeichert"}

    Raises:
        HTTPException: 404 wenn Alarm nicht gefunden
        HTTPException: 500 bei Email-Fehler
    """
    try:
        # Alarm aus DB holen
        alarme = datenbank.alle_alarme_abrufen(1000)
        alarm = next((a for a in alarme if a["id"] == alarm_id), None)
        if not alarm:
            raise HTTPException(status_code=404, detail="Alarm nicht gefunden")

        # Alarm-Objekt für EmailNotifier erstellen
        from .alarm_engine import Alarm
        alarm_obj = Alarm(
            sensor_id=alarm["sensor_id"],
            alarm_typ=alarm["alarm_typ"],
            nachricht=alarm["nachricht"],
            wert=alarm["wert"],
            schwellwert=alarm["schwellwert"],
            id=alarm_id
        )

        # Email senden (speichert automatisch in DB, auch bei SMTP-Fehler)
        email_notifier = alarm_engine._notifier[0]  # EmailNotifier
        email_notifier.senden(alarm_obj)

        # Email wurde in DB gespeichert (mit Status 'ausstehend' oder 'fehlgeschlagen')
        # Das zählt als Erfolg - der User sieht das Ergebnis in der Email-Liste
        return {"status": "erfolgreich", "alarm_id": alarm_id, "hinweis": "Email wurde gespeichert"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email senden Fehler: {e}")
        raise HTTPException(status_code=500, detail="Email senden fehlgeschlagen")


@app.get("/alarm-emails")
async def alarm_emails_liste(limit: int = Query(default=100, ge=1, le=1000)):
    """
    Alle gesendeten Alarm-Emails abrufen.

    Gibt Emails mit Status und Antwort-Information zurück.

    Args:
        limit: Maximale Anzahl (1-1000, standard: 100)

    Returns:
        Liste von Emails mit:
        - id, alarm_id, sensor_id, alarm_typ, nachricht
        - empfaenger, subject, sende_status, error_message
        - hat_geantwortet, anzahl_antworten
        - created_at, alarm_zeitstempel

    Raises:
        HTTPException: Bei Datenbankfehler (500)
    """
    try:
        emails = datenbank.alle_alarm_emails_abrufen(limit)
        ergebnis = []
        for e in emails:
            # Antworten für diese Email abrufen
            antworten = datenbank.alarm_email_antworten_abrufen(e["id"])
            hat_geantwortet = len(antworten) > 0
            ergebnis.append({
                "id": e["id"],
                "alarm_id": e["alarm_id"],
                "sensor_id": e.get("sensor_id"),
                "alarm_typ": e.get("alarm_typ"),
                "nachricht": e.get("nachricht"),
                "empfaenger": e["empfaenger"],
                "subject": e["subject"],
                "sende_status": e["sende_status"],
                "error_message": e.get("error_message"),
                "hat_geantwortet": hat_geantwortet,
                "anzahl_antworten": len(antworten),
                "created_at": str(e["created_at"]),
                "alarm_zeitstempel": str(e.get("alarm_zeitstempel")) if e.get("alarm_zeitstempel") else None,
            })
        return ergebnis
    except Exception as e:
        logger.error(f"Alarm-Emails Fehler: {e}")
        raise HTTPException(status_code=500, detail="Datenbankfehler")


# =============================================================================
# KONFIGURATION ENDPOINTS (laut Pflichtenheft)
# =============================================================================

@app.get("/konfiguration")
async def konfiguration_liste():
    """
    Alle System-Konfigurationen abrufen.

    Gibt alle Schlüssel-Wert-Paare der Systemkonfiguration zurück.

    Returns:
        Liste von Konfigurationen mit schluessel, wert, beschreibung

    Raises:
        HTTPException: Bei Datenbankfehler (500)
    """
    try:
        configs = datenbank.alle_system_konfiguration_abrufen()
        return [{
            "schluessel": c["konfiguration_schluessel"],
            "wert": c["wert"],
            "beschreibung": c.get("beschreibung"),
        } for c in configs]
    except Exception as e:
        logger.error(f"Konfiguration Fehler: {e}")
        raise HTTPException(status_code=500, detail="Datenbankfehler")


@app.put("/konfiguration")
async def konfiguration_aendern(schluessel: str, wert: str, beschreibung: str = None):
    """
    System-Konfiguration erstellen oder aktualisieren.

    Verwendet INSERT ... ON DUPLICATE KEY UPDATE für automatisches
    Update bei existierendem Schlüssel.

    Args:
        schluessel:   Konfigurationsschlüssel
        wert:         Neuer Wert
        beschreibung: Optionalle Beschreibung

    Returns:
        {"status": "erfolgreich", "schluessel": schluessel}

    Raises:
        HTTPException: Bei Speicherfehler (500)
    """
    if datenbank.system_konfiguration_speichern(schluessel, wert, beschreibung):
        return {"status": "erfolgreich", "schluessel": schluessel}
    raise HTTPException(status_code=500, detail="Speichern fehlgeschlagen")


@app.get("/alarm_konfiguration")
async def alarm_konfiguration_liste():
    """
    Alle Alarm-Konfigurationen abrufen.

    Gibt Schwellwerte und aktivierte Alarmierungen für alle Sensoren zurück.

    Returns:
        Liste von Alarm-Konfigurationen mit:
        - sensor_id, sensor_name, alarm_typ
        - schwellwert_min, schwellwert_max
        - alarmierung_email, alarmierung_led, alarmierung_buzzer, alarmierung_dashboard

    Raises:
        HTTPException: Bei Datenbankfehler (500)
    """
    try:
        configs = datenbank.alle_alarm_konfigurationen_abrufen()
        return [{
            "sensor_id": c["sensor_id"],
            "sensor_name": c.get("sensor_name"),
            "alarm_typ": c["alarm_typ"],
            "schwellwert_min": c.get("schwellwert_min"),
            "schwellwert_max": c.get("schwellwert_max"),
            "alarmierung_email": c.get("alarmierung_email"),
            "alarmierung_led": c.get("alarmierung_led"),
            "alarmierung_buzzer": c.get("alarmierung_buzzer"),
            "alarmierung_dashboard": c.get("alarmierung_dashboard"),
        } for c in configs]
    except Exception as e:
        logger.error(f"Alarm-Konfiguration Fehler: {e}")
        raise HTTPException(status_code=500, detail="Datenbankfehler")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=config.api.host, port=config.api.port, reload=config.api.debug)
