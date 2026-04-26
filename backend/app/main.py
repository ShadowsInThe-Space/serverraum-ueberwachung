"""
FastAPI Backend für Serverraum-Überwachung
=========================================

Starten mit:
    uvicorn app.main:app --host 0.0.0.0 --port 8000

@author Marc-Dennis Haberland
@date 04.03.2026
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

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")


# =============================================================================
# Response Models
# =============================================================================

@dataclass
class SensorResponse:
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
        alarm = alarm_engine.pruefe_alarm(sensor_id, sensor_typ, wert)
        if alarm:
            alarm_engine.alarm_ausloesen(alarm)

    mqtt_client.set_alarm_callback(on_sensor_data)

    yield

    logger.info("Backend shutdown...")
    mqtt_client.trennen()
    datenbank.trennen()
    alarm_engine.cleanup()


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(title="Serverraum-Überwachung API", version="1.0.0", lifespan=lifespan)

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
    logger.error(f"Exception: {exc}")
    return error_response(
        "internal_error", str(exc) if config.api.debug else "Interner Fehler", 500
    )


# =============================================================================
# Static Files
# =============================================================================

if os.path.exists(STATIC_DIR):
    from fastapi.staticfiles import StaticFiles
    # Mount /static for JS/CSS and /js directly for compatibility
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.mount("/js", StaticFiles(directory=os.path.join(STATIC_DIR, "js")), name="js")


# =============================================================================
# API Endpunkte
# =============================================================================

@app.get("/")
async def root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        from fastapi.responses import FileResponse
        return FileResponse(index_path)
    return {"name": "Serverraum-Überwachung API", "version": "1.0.0", "status": "online"}


@app.get("/status")
async def status():
    aktive_alarme = datenbank.aktive_alarme_abrufen()
    return {
        "status": "online",
        "mqtt_verbunden": mqtt_client.ist_verbunden,
        "datenbank_verbunden": datenbank.connection is not None,
        "aktive_alarme": len(aktive_alarme),
    }


@app.get("/sensoren")
async def sensoren_liste():
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
    messungen = datenbank.letzte_messungen_abrufen(sensor_id, limit)
    return [{"wert": m["wert"], "timestamp": str(m["timestamp"])} for m in messungen]


@app.get("/sensoren/{sensor_id}/statistik")
async def statistik(sensor_id: str, stunden: int = Query(default=24, ge=1, le=168)):
    stat = datenbank.statistik_abrufen(sensor_id, stunden)
    return {"sensor_id": sensor_id, **stat}


@app.get("/alarme")
async def alarme(status: Optional[str] = None, limit: int = Query(default=100, ge=1, le=1000)):
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
    if datenbank.alarm_quittieren(alarm_id):
        return {"status": "erfolgreich", "alarm_id": alarm_id}
    raise HTTPException(status_code=500, detail="Quittieren fehlgeschlagen")


@app.delete("/alarme/{alarm_id}")
async def alarm_loeschen(alarm_id: int):
    """Löscht einen Alarm vollständig"""
    if datenbank.alarm_loeschen(alarm_id):
        return {"status": "erfolgreich", "alarm_id": alarm_id}
    raise HTTPException(status_code=500, detail="Löschen fehlgeschlagen")


@app.post("/alarme/{alarm_id}/email")
async def alarm_email_senden(alarm_id: int):
    """Sendet eine Erinnerungs-Email für einen Alarm"""
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
    """Alle gesendeten Alarm-Emails abrufen mit Antwort-Status"""
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
    """Alle System-Konfigurationen abrufen"""
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
    """System-Konfiguration ändern"""
    if datenbank.system_konfiguration_speichern(schluessel, wert, beschreibung):
        return {"status": "erfolgreich", "schluessel": schluessel}
    raise HTTPException(status_code=500, detail="Speichern fehlgeschlagen")


@app.get("/alarm_konfiguration")
async def alarm_konfiguration_liste():
    """Alle Alarm-Konfigurationen abrufen"""
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
