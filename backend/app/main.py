"""
FastAPI Backend für Serverraum-Überwachung
==========================================

Hauptprogramm des Backends:
- MQTT-Client (empfängt Sensor-Daten)
- REST-API (Frontend fragt Daten ab)
- Datenbank-Verbindung
- Alarm-Engine (Schwellwert-Überwachung)

Starten mit:
    uvicorn app.main:app --host 0.0.0.0 --port 8000

Oder:
    python -m app.main

@author Marc-Dennis Haberland
@date 04.03.2026
Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
"""

import logging
import uuid
from contextlib import asynccontextmanager
from typing import List, Optional, Any
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from . import config
from .mqtt_client import mqtt_client
from .db import datenbank
from .alarm_engine import alarm_engine

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Custom HTTPException Klassen
# ============================================================================

class ServerraumHTTPException(HTTPException):
    """Basisklasse für alle Serverraum-spezifischen Exceptions"""

    def __init__(self, status_code: int, detail: str, error_type: str = "server_error"):
        super().__init__(status_code=status_code, detail=detail)
        self.error_type = error_type


class SensorNichtGefundenException(ServerraumHTTPException):
    """Exception wenn ein Sensor nicht gefunden wird"""

    def __init__(self, sensor_id: str):
        super().__init__(
            status_code=404,
            detail=f"Sensor mit ID '{sensor_id}' nicht gefunden",
            error_type="sensor_not_found"
        )


class AlarmNichtGefundenException(ServerraumHTTPException):
    """Exception wenn ein Alarm nicht gefunden wird"""

    def __init__(self, alarm_id: int):
        super().__init__(
            status_code=404,
            detail=f"Alarm mit ID '{alarm_id}' nicht gefunden",
            error_type="alarm_not_found"
        )


class DatenbankVerbindungsException(ServerraumHTTPException):
    """Exception bei Datenbankverbindungsproblemen"""

    def __init__(self, detail: str = "Datenbankverbindung fehlgeschlagen"):
        super().__init__(
            status_code=503,
            detail=detail,
            error_type="database_connection_error"
        )


class MQTTVerbindungsException(ServerraumHTTPException):
    """Exception bei MQTT-Verbindungsproblemen"""

    def __init__(self, detail: str = "MQTT-Verbindung fehlgeschlagen"):
        super().__init__(
            status_code=503,
            detail=detail,
            error_type="mqtt_connection_error"
        )


class ValidierungsException(ServerraumHTTPException):
    """Exception bei Validierungsfehlern"""

    def __init__(self, detail: str):
        super().__init__(
            status_code=422,
            detail=detail,
            error_type="validation_error"
        )


# ============================================================================
# Request ID Middleware & Context
# ============================================================================

# Request ID Context (vor App Definition)
class RequestContext:
    """Thread-safe Request Context für Request ID"""
    _request_id: str = "no-request"

    @classmethod
    def set_request_id(cls, request_id: str):
        cls._request_id = request_id

    @classmethod
    def get_request_id(cls) -> str:
        return cls._request_id


# ============================================================================
# Strukturierte Error Response
# ============================================================================

class ErrorResponse(BaseModel):
    """Standardisiertes Error Response Format"""
    error: str
    detail: str
    status_code: int
    request_id: Optional[str] = None


def create_error_response(
    error: str,
    detail: str,
    status_code: int,
    request_id: Optional[str] = None
) -> JSONResponse:
    """
    Erstellt eine standardisierte Error Response

    Format: {"error": "message", "detail": "...", "status_code": 500, "request_id": "..."}
    """
    content = ErrorResponse(
        error=error,
        detail=detail,
        status_code=status_code,
        request_id=request_id or RequestContext.get_request_id()
    )
    return JSONResponse(
        status_code=status_code,
        content=content.model_dump()
    )


# ============================================================================
# Startup und Shutdown
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup und Shutdown Logik für FastAPI
    Wird automatisch beim Starten/Beenden aufgerufen
    """
    # Startup
    logger.info("=== Serverraum-Überwachung Backend startet ===")

    # Datenbank verbinden
    if datenbank.verbinden():
        logger.info("Datenbank verbunden")
    else:
        logger.error("Datenbank-Verbindung fehlgeschlagen!")

    # MQTT verbinden
    if mqtt_client.verbinden():
        logger.info("MQTT verbunden")
    else:
        logger.error("MQTT-Verbindung fehlgeschlagen!")

    # Alarm-Engine initialisieren (GPIO)
    alarm_engine.initialisiere_gpio()

    # MQTT Callback für Alarme setzen
    def alarm_callback(sensor_id: str, sensor_typ: str, wert: float,
                     ist_esp32_alarm: bool = False):
        """
        Callback wenn neue Sensor-Daten empfangen werden
        Prüft Schwellwerte und löst ggf. Alarm aus
        """
        if ist_esp32_alarm:
            # ESP32 hat selbst Alarm ausgelöst
            return

        # Prüfe Schwellwerte
        alarm = alarm_engine.pruefe_alarm(sensor_id, sensor_typ, wert)
        if alarm:
            alarm_engine.alarm_ausloesen(alarm)

    mqtt_client.set_alarm_callback(alarm_callback)

    yield  # Hier läuft die Anwendung

    # Shutdown
    logger.info("=== Backend wird heruntergefahren ===")

    mqtt_client.trennen()
    datenbank.trennen()
    alarm_engine.cleanup()


# ============================================================================
# FastAPI App erstellen
# ============================================================================

app = FastAPI(
    title="Serverraum-Überwachung API",
    description="REST-API für das Serverraum-Überwachungssystem",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# Globale Exception Handler
# ============================================================================

@app.exception_handler(ServerraumHTTPException)
async def serverraum_http_exception_handler(request: Request, exc: ServerraumHTTPException):
    """
    Handler für alle Serverraum-spezifischen HTTP Exceptions
    """
    logger.error(
        f"ServerraumHTTPException: {exc.error_type} - {exc.detail} "
        f"[{RequestContext.get_request_id()}]"
    )
    return create_error_response(
        error=exc.error_type,
        detail=exc.detail,
        status_code=exc.status_code
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handler für Standard FastAPI HTTPException (404, 422, 500 etc.)
    """
    error_type = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        422: "validation_error",
        500: "internal_server_error",
        502: "bad_gateway",
        503: "service_unavailable"
    }.get(exc.status_code, "http_error")

    logger.warning(
        f"HTTPException: {error_type} ({exc.status_code}) - {exc.detail} "
        f"[{RequestContext.get_request_id()}]"
    )
    return create_error_response(
        error=error_type,
        detail=exc.detail,
        status_code=exc.status_code
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Generic Exception Handler für alle unhandled Exceptions
    Fängt alle Exceptions ab die nicht vorher behandelt wurden
    """
    request_id = RequestContext.get_request_id()
    logger.critical(
        f"Unhandled Exception: {type(exc).__name__}: {str(exc)} "
        f"[{request_id}] Path: {request.url.path}"
    )

    # Stacktrace im Debug-Modus
    debug_mode = getattr(getattr(config, 'api', None), 'debug', False) if hasattr(config, 'api') else False
    if debug_mode:
        import traceback
        detail = f"{type(exc).__name__}: {str(exc)}\n{traceback.format_exc()}"
    else:
        detail = "Ein unerwarteter Fehler ist aufgetreten"

    return create_error_response(
        error="internal_server_error",
        detail=detail,
        status_code=500
    )


# ============================================================================
# Request ID Middleware (nach Exception Handlern)
# ============================================================================

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """
    Middleware die jede Anfrage mit einer Request ID versieht
    Header: X-Request-ID
    """
    # Request ID aus Header holen oder neue generieren
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    RequestContext.set_request_id(request_id)

    # Request ID als Response Header setzen
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


# Static files für Frontend
from fastapi.staticfiles import StaticFiles
import os
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# CORS - erlaubt alle Origins für Entwicklung
cors_env = os.getenv("CORS_ORIGINS", "")
allowed_origins = [o.strip() for o in cors_env.split(",") if o.strip()]
if not allowed_origins:
    allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Datenmodelle (Pydantic)
# ============================================================================

class SensorResponse(BaseModel):
    """Response-Modell für Sensor-Informationen"""
    sensor_id: str
    sensor_typ: str
    name: Optional[str] = None
    aktiviert: bool
    letzte_messung: Optional[float] = None
    letzte_zeit: Optional[str] = None


class MessungResponse(BaseModel):
    """Response-Modell für Messungen"""
    wert: float
    status: str
    timestamp: str


class AlarmResponse(BaseModel):
    """Response-Modell für Alarme"""
    id: int
    sensor_id: str
    alarm_typ: str
    nachricht: str
    wert: float
    schwellwert: float
    status: str
    created_at: str
    quittiert_at: Optional[str] = None


class StatistikResponse(BaseModel):
    """Response-Modell für Statistik"""
    sensor_id: str
    min: float
    max: float
    durchschnitt: float
    anzahl: int


class SystemStatusResponse(BaseModel):
    """Response-Modell für System-Status"""
    status: str
    mqtt_verbunden: bool
    datenbank_verbunden: bool
    aktive_alarme: int


# ============================================================================
# API Endpunkte
# ============================================================================

@app.get("/", tags=["System"])
async def root():
    """Frontend HTML"""
    import os
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        from fastapi.responses import FileResponse
        return FileResponse(index_path)
    return {
        "name": "Serverraum-Überwachung API",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/status", response_model=SystemStatusResponse, tags=["System"])
async def system_status():
    """
    Gibt den aktuellen System-Status zurück

    Zeigt ob MQTT und Datenbank verbunden sind
    """
    # Zähle aktive Alarme
    aktive_alarme = datenbank.aktive_alarme_abrufen()

    return {
        "status": "online",
        "mqtt_verbunden": mqtt_client.ist_verbunden,
        "datenbank_verbunden": datenbank.connection is not None,
        "aktive_alarme": len(aktive_alarme)
    }


@app.get("/sensoren", response_model=List[SensorResponse], tags=["Sensoren"])
async def sensoren_liste():
    """
    Gibt Liste aller Sensoren zurück

    Zeigt alle registrierten Sensoren mit ihren letzten Messwerten
    """
    try:
        # Hole alle Sensoren aus Datenbank
        datenbank.cursor.execute("""
            SELECT sensor_id, sensor_typ, name, aktiviert
            FROM sensoren
            ORDER BY created_at DESC
        """)
        sensoren = datenbank.cursor.fetchall()

        ergebnis = []
        for sensor in sensoren:
            # Hole letzte Messung
            messungen = datenbank.letzte_messungen_abrufen(sensor['sensor_id'], 1)

            letzte_messung = None
            letzte_zeit = None
            if messungen:
                letzte_messung = messungen[0]['wert']
                letzte_zeit = str(messungen[0]['timestamp'])

            ergebnis.append({
                "sensor_id": sensor['sensor_id'],
                "sensor_typ": sensor['sensor_typ'],
                "name": sensor['name'],
                "aktiviert": bool(sensor['aktiviert']),
                "letzte_messung": letzte_messung,
                "letzte_zeit": letzte_zeit
            })

        return ergebnis

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Sensoren: {e}")
        # Im Development-Modus werden Details zurückgegeben, im Produktionsmodus nur eine generische Meldung
        if config.api.debug:
            raise HTTPException(status_code=500, detail=f"Datenbankfehler: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail="Datenbankfehler")


@app.get("/sensoren/{sensor_id}/messungen", response_model=List[MessungResponse], tags=["Sensoren"])
async def messungen_liste(
    sensor_id: str,
    limit: int = Query(default=100, ge=1, le=1000)
):
    """
    Gibt Messungen für einen Sensor zurück

    @param sensor_id ID des Sensors
    @param limit Anzahl der Messungen (max 1000)
    """
    try:
        messungen = datenbank.letzte_messungen_abrufen(sensor_id, limit)

        return [
            {
                "wert": m['wert'],
                "status": m['status'],
                "timestamp": str(m['timestamp'])
            }
            for m in messungen
        ]

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Messungen: {e}")
        if config.api.debug:
            raise HTTPException(status_code=500, detail=f"Datenbankfehler: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail="Datenbankfehler")


@app.get("/sensoren/{sensor_id}/statistik", response_model=StatistikResponse, tags=["Sensoren"])
async def statistik(
    sensor_id: str,
    stunden: int = Query(default=24, ge=1, le=168)
):
    """
    Gibt Statistik für einen Sensor zurück

    @param sensor_id ID des Sensors
    @param stunden Zeitraum in Stunden (max 168 = 1 Woche)
    """
    try:
        stat = datenbank.statistik_abrufen(sensor_id, stunden)

        return {
            "sensor_id": sensor_id,
            "min": stat['min'],
            "max": stat['max'],
            "durchschnitt": stat['durchschnitt'],
            "anzahl": stat['anzahl']
        }

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Statistik: {e}")
        if config.api.debug:
            raise HTTPException(status_code=500, detail=f"Datenbankfehler: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail="Datenbankfehler")


@app.get("/alarme", response_model=List[AlarmResponse], tags=["Alarme"])
async def alarme_liste(
    status: Optional[str] = Query(default=None, description="Filter: aktiv, quittiert, alle"),
    limit: int = Query(default=100, ge=1, le=1000)
):
    """
    Gibt Liste der Alarme zurück

    @param status Filter nach Status (optional)
    @param limit Anzahl der Alarme
    """
    try:
        if status == "aktiv":
            alarme = datenbank.aktive_alarme_abrufen()
        else:
            alarme = datenbank.alle_alarme_abrufen(limit)

        ergebnis = []
        for alarm in alarme:
            ergebnis.append({
                "id": alarm['id'],
                "sensor_id": alarm['sensor_id'],
                "alarm_typ": alarm['alarm_typ'],
                "nachricht": alarm['nachricht'],
                "wert": alarm['wert'],
                "schwellwert": alarm['schwellwert'],
                "status": alarm['status'],
                "created_at": str(alarm['created_at']),
                "quittiert_at": str(alarm['quittiert_at']) if alarm.get('quittiert_at') else None
            })

        return ergebnis

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Alarme: {e}")
        raise HTTPException(status_code=500, detail="Datenbankfehler")


@app.post("/alarme/{alarm_id}/quittieren", tags=["Alarme"])
async def alarm_quittieren(alarm_id: int):
    """
    Quittiert einen Alarm

    @param alarm_id ID des zu quittierenden Alarms
    """
    try:
        if datenbank.alarm_quittieren(alarm_id):
            return {"status": "erfolgreich", "alarm_id": alarm_id}
        else:
            raise HTTPException(status_code=500, detail="Quittieren fehlgeschlagen")

    except Exception as e:
        logger.error(f"Fehler beim Quittieren: {e}")
        raise HTTPException(status_code=500, detail="Datenbankfehler")


# ============================================================================
# Main (für direktes Ausführen)
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Lade Konfiguration aus Umgebung
    config.lade_konfiguration_aus_env()

    # Starte Server
    uvicorn.run(
        "app.main:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.debug
    )
