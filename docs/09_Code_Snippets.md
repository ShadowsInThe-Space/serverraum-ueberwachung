# Code-Snippets – Serverraum-Überwachung

> Kurze, fokussierte Code-Abschnitte für die Projektdokumentation.

---

## 1. Polymorphie: Sensor-Hierarchie

**Datei:** `firmware/include/sensors/Sensor.h`

```cpp
// Abstrakte Basisklasse – Polymorphie in Aktion
class Sensor
{
public:
    Sensor(int gpioPin, String sensorId, SensorTyp typ, 
           unsigned long intervall, bool aktiviert)
        : letzterMessZeitpunkt(0)
    {
        konfiguration = {gpioPin, sensorId, typ, intervall, aktiviert};
        messwert = {sensorId, typ, 0.0f, SensorStatus::NICHT_VERFUEGBAR, 0};
    }

    virtual ~Sensor() = default;          // Wichtig für Vererbung!
    virtual bool init() = 0;             // = 0 macht sie "rein virtuell"
    virtual bool messen() = 0;           // Jeder Sensor anders
    SensorMesswert getMesswert() const { return messwert; }

protected:
    void aktualisiereMesswert(float wert, SensorStatus status)
    {
        messwert.wert = wert;
        messwert.status = status;
        messwert.timestamp = millis();
    }

    SensorKonfiguration konfiguration;
    SensorMesswert messwert;
    unsigned long letzterMessZeitpunkt;
};
```

**Konkrete Implementierung (z.B. DS18B20):**
```cpp
class DS18B20Sensor : public Sensor {  // Vererbung
public:
    DS18B20Sensor(int pin, const String& name, unsigned long intervall)
        : Sensor(pin, name, SensorTyp::DS18B20, intervall, true),
          oneWire(pin), sensors(&oneWire) {}

    bool init() override {
        sensors.begin();
        return sensors.getDeviceCount() > 0;
    }

    bool messen() override {                          // Override = Polymorphie
        sensors.requestTemperatures();
        aktualisiereMesswert(sensors.getTempCByIndex(0), SensorStatus::OK);
        return true;
    }

private:
    OneWire oneWire;
    DallasTemperature sensors;
};
```

**Verwendung im SensorManager:**
```cpp
std::vector<Sensor*> sensoren;  // Alle Sensoren in einer Liste!

// Polymorphie: Verschiedene Typen, gleiche Behandlung
for (auto& s : sensoren) {
    s->init();   // Jeder initialisiert sich selbst
    s->messen(); // Jeder misst anders
}
```

---

## 2. Business-Logik: Alarm-System

**Datei:** `backend/app/alarm_engine.py`

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Alarm:
    sensor_id: str
    alarm_typ: str
    nachricht: str
    wert: float
    schwellwert: float

class SpamSchutz:
    """Verhindert Alarm-Flut bei dauerhaftem Problem."""
    def __init__(self, abstand: int = 60):
        self.abstand = abstand
        self._letzte = {}

    def ist_erlaubt(self, key: str) -> bool:
        jetzt = time.time()
        if key in self._letzte and jetzt - self._letzte[key] < self.abstand:
            return False  # Zu früh!
        self._letzte[key] = jetzt
        return True

class AlarmEngine:
    def __init__(self):
        self._spam = SpamSchutz(60)
        self._notifier = [EmailNotifier(), GPIODeviceNotifier(...), DashboardNotifier()]

    def pruefe_alarm(self, sensor_id: str, sensor_typ: str, wert: float) -> Optional[Alarm]:
        # Grenzwert-Prüfung
        if sensor_typ == "DS18B20":
            if wert > 30.0:
                return Alarm(sensor_id, "TEMPERATUR_HOCH", f"Zu hoch: {wert}°C", wert, 30.0)
        elif sensor_typ == "MQ2" and wert > 200.0:
            return Alarm(sensor_id, "RAUCHGAS", f"Rauchgas: {wert} ppm", wert, 200.0)
        return None

    def alarm_ausloesen(self, alarm: Alarm):
        key = f"{alarm.sensor_id}_{alarm.alarm_typ}"
        if not self._spam.ist_erlaubt(key):
            return  # Spam-Schutz!
        
        datenbank.alarm_speichern(...)  # In DB speichern
        
        for n in self._notifier:         # Alle Benachrichtigungskanäle
            n.senden(alarm)
```

---

## 3. Datenbank: Connection Pooling

**Datei:** `backend/app/db.py`

```python
from mysql.connector import pooling

_pool = None

def _get_pool():
    """Connection Pool – wird einmal erstellt, dann wiederverwendet."""
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="serverraum_pool",
            pool_size=5,                    # 5 parallele Verbindungen
            host=config.datenbank.host,
            user=config.datenbank.benutzer,
            password=config.datenbank.passwort,
            database=config.datenbank.datenbank,
        )
    return _pool

def _query(sql: str, params: tuple = ()):
    """SELECT mit Parameter-Escaping (Schutz vor SQL-Injection!)."""
    conn = _get_pool().get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params)           # %s wird sicher ersetzt!
        return cursor.fetchall()
    finally:
        conn.close()                        # Immer schließen!

class Datenbank:
    def messung_speichern(self, sensor_id: str, wert: float, status: str) -> bool:
        result = _query("SELECT id FROM sensoren WHERE sensor_id = %s", (sensor_id,))
        if not result:
            return False
        return _execute(
            "INSERT INTO messungen (sensor_id, wert, status, timestamp) VALUES (%s, %s, %s, NOW())",
            (result[0]["id"], wert, status)
        )

    def statistik_abrufen(self, sensor_id: str, stunden: int = 24) -> dict:
        """SQL mit AVG, MIN, MAX Aggregation."""
        result = _query("""
            SELECT MIN(wert) as min, MAX(wert) as max,
                   AVG(wert) as durchschnitt, COUNT(*) as anzahl
            FROM messungen m
            JOIN sensoren s ON m.sensor_id = s.id
            WHERE s.sensor_id = %s 
              AND m.timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
        """, (sensor_id, stunden))
        
        if result and result[0]["min"]:
            r = result[0]
            return {"min": float(r["min"]), "max": float(r["max"]),
                    "durchschnitt": float(r["durchschnitt"]), "anzahl": int(r["anzahl"])}
        return {"min": 0, "max": 0, "durchschnitt": 0, "anzahl": 0}
```

---

## 4. ESP32: Sensor-Initialisierung

**Datei:** `firmware/src/main.cpp`

```cpp
// Hardware-Pins
#define PIN_DS18B20 4
#define PIN_PIR 21
#define PIN_MQ2 1
#define PIN_SHT31_SCL 9
#define PIN_SHT31_SDA 6

// Globale Instanzen
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
SensorManager* sensorManager = nullptr;

void initSensoren() {
    Serial.println("Sensoren initialisieren...");
    
    // SensorManager erstellen
    sensorManager = new SensorManager(mqttClient, MQTT_TOPIC_BASE);

    // Sensoren hinzufügen – Polymorphie in Aktion!
    // Alle werden als Sensor* behandelt, obwohl sie verschieden sind.
    auto ds18b20 = new DS18B20Sensor(PIN_DS18B20, "temp_serverraum", 10000);
    sensorManager->sensorHinzufuegen(ds18b20);

    auto pir = new PIRSensor(PIN_PIR, "bewegung", 10000);
    sensorManager->sensorHinzufuegen(pir);

    auto mq2 = new MQ2Sensor(PIN_MQ2, "rauchgas", 10000);
    mq2->setzeSchwellwert(200.0f);
    sensorManager->sensorHinzufuegen(mq2);

    // Alle auf einmal initialisieren
    sensorManager->init();
}

void loop() {
    if (!mqttClient.connected()) {
        verbindeMQTT();
    }
    mqttClient.loop();
    
    // Automatisch alle Sensoren auslesen + per MQTT senden
    sensorManager->messenUndPublishen();
}
```

---

## Zusammenfassung

| Konzept | Snippet | Zeigt |
|---------|---------|-------|
| **OOP / Polymorphie** | 1, 4 | Abstrakte Klasse, Vererbung, virtuellen Methoden |
| **Connection Pooling** | 3 | DB-Verbindungen wiederverwenden |
| **SQL** | 3 | Parameter-Escaping, Aggregation |
| **Business-Logik** | 2 | Spam-Schutz, Trennung Prüfung/Benachrichtigung |
| **IoT / Embedded** | 4 | Sensor-Ansteuerung, MQTT |
