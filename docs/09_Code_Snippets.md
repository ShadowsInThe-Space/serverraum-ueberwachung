# Code-Snippets – Serverraum-Überwachung

> Kurze, fokussierte Code-Abschnitte für die Projektdokumentation. Hier wurden die 4 aussagekräftigsten Snippets ausgewählt, um die Systemarchitektur (Sensor-Erfassung, MQTT-Kommunikation, Geschäftslogik und Fehlerbehandlung) ideal für die Prüfer zu demonstrieren.

---

## 1. Datenstrukturen der Firmware (C++)

**Datei (Auszug):** `firmware/include/sensors/SensorData.h`

<!-- *Begründung für die Auswahl: Zeigt den strukturierten Ansatz in der Firmware 
mit typensicheren Enums und klaren Structs für Messwerte. Dies belegt 
fundierte C++-Kenntnisse und eine saubere Kapselung der Sensordaten.* -->

```cpp
enum class SensorTyp
{
    DS18B20,     ///< Digitaler 1-Wire Temperatursensor
    SHT31,       ///< I2C Temperatursensor und Feuchtigkeitssensor
    MQ2,         ///< Analoger Sensor für Rauchgas und brennbare Gase
    PIR          ///< Passiver Infrarot-Bewegungsmelder
};

enum class SensorStatus
{
    OK,              ///< Sensor funktioniert normal
    FEHLER,          ///< Allgemeiner Sensorfehler
    TIMEOUT,         ///< Kommunikationstimeout (bei digitalen Sensoren)
    NICHT_VERFUEGBAR ///< Sensor nicht angeschlossen oder defekt
};

struct SensorMesswert
{
    String sensorId;           ///< Eindeutige Sensor-ID
    SensorTyp sensorTyp;       ///< Sensor-Typ
    float wert;                ///< Messwert (Temperatur in °C, Feuchte in %, etc.)
    SensorStatus status;       ///< Sensor-Status
    unsigned long timestamp;   ///< Zeitstempel in Millisekunden
};
```

---

## 2. Kommunikationsschnittstelle: MQTT-Listener & Routing (Python)

**Datei:** `backend/app/mqtt_client.py`

**Sprechtext (Folie):**
"Unser MQTT-Basis-Topic ist zweistufig: `serverraum/sensor`. Deshalb liegt die `sensor_id` nach `split('/')` an Index 2; Index 3 ist optional der Nachrichtentyp wie `data`, `alarm` oder `status`. Das Mapping ist also: `[0]=serverraum`, `[1]=sensor`, `[2]=sensor_id`, `[3]=msg_typ`."

<!-- *Begründung für die Auswahl: Bildet die Brücke zwischen Hardware und Backend ab. 
Zeigt Event-Driven-Architecture, dynamisches Routing der Topics, JSON-Parsing mit 
Exception-Handling und die saubere Weiterleitung an die Datenbank sowie die Alarmierungs-Logik.* -->

```python
    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            if not topic.startswith(config.mqtt.topic_basis):
                return

            teile = topic.split("/")
            if len(teile) < 3: return

            sensor_id = teile[2]
            msg_typ = teile[3] if len(teile) > 3 else "data"

            try:
                daten = json.loads(msg.payload.decode("utf-8"))
            except json.JSONDecodeError:
                logger.error(f"JSON Fehler: {msg.payload}")
                return

            # Routing je nach Nachrichtentyp
            if msg_typ == "alarm":
                self._verarbeite_alarm(sensor_id, daten)
            elif msg_typ == "status":
                logger.info(f"ESP32-S3 Status: {daten.get('status')}")
            else:
                self._verarbeite_daten(sensor_id, daten)

        except Exception as e:
            logger.error(f"Message Fehler: {e}")

    def _verarbeite_daten(self, sensor_id: str, daten: dict):
        try:
            sensor_typ = daten.get("sensor_typ", "UNBEKANNT")
            wert = float(daten.get("wert", 0))
            status = daten.get("status", "OK")
            einheit = daten.get("einheit")

            # 1. Daten via DAO in MariaDB persistieren
            datenbank.sensor_speichern(sensor_id, sensor_typ)
            datenbank.messung_speichern(sensor_id, wert, status, einheit)

            # 2. Alarm-Engine via Callback triggern
            if self.alarm_callback:
                self.alarm_callback(sensor_id, sensor_typ, wert)

        except Exception as e:
            logger.error(f"Datenverarbeitung Fehler: {e}")
```

---

## 3. Haupt-Geschäftslogik: Alarm-Engine (Python)

**Datei (Auszug):** `backend/app/alarm_engine.py`

> Hinweis: Für die Projektdokumentation ist dieser Ausschnitt bewusst auf die im Fließtext beschriebenen Kernfälle (Temperatur + MQ2) fokussiert.

<!-- *Begründung für die Auswahl: Bildet das Herzstück des Systems ab. 
Zeigt saubere Objektorientierung (OOP), Entkopplung durch Delegation 
an Notifier-Klassen und eine nachvollziehbare Business-Logik zur Schwellwertprüfung.*
 -->
```python
class AlarmEngine:
    def __init__(self):
        self._spam = SpamSchutz(abstand_sekunden=60)
        
        # Liste aller aktiven Notifier (Multi-Channel Alarmierung)
        self._notifier = [
            EmailNotifier(),
            GPIODeviceNotifier(config.alarm.led_pin, "LED", 5.0),
            GPIODeviceNotifier(config.alarm.buzzer_pin, "BUZZER", 2.0),
            DashboardNotifier(),
        ]

    def pruefe_alarm(self, sensor_id: str, sensor_typ: str, wert: float) -> Optional[Alarm]:
        # Temperatur Schwellwertprüfung
        if sensor_typ in ["DS18B20", "SHT31"]:
            if wert > config.alarm.temperatur_max:
                return Alarm(sensor_id, "TEMPERATUR_HOCH", f"Temperatur zu hoch: {wert:.1f}°C", wert, config.alarm.temperatur_max)
        
        # Rauchgas Schwellwertprüfung
        elif sensor_typ == "MQ2" and wert > config.alarm.rauchgas_max:
            return Alarm(sensor_id, "RAUCHGAS", f"Rauchgas: {wert:.0f} ppm", wert, config.alarm.rauchgas_max)
            
        return None

    def alarm_ausloesen(self, alarm: Alarm):
        alarm_key = f"{alarm.sensor_id}_{alarm.alarm_typ}"
        
        # Spam-Schutz zur Vermeidung von Floodings (Entprellen)
        if not self._spam.ist_erlaubt(alarm_key):
            return

        logger.warning(f"ALARM: {alarm.nachricht}")
        
        # In Datenbank persistieren
        alarm.id = datenbank.alarm_speichern(
            sensor_id=alarm.sensor_id, alarm_typ=alarm.alarm_typ,
            nachricht=alarm.nachricht, wert=alarm.wert, schwellwert=alarm.schwellwert
        )

        # Alle konfigurierten Notifier auslösen
        for n in self._notifier:
            try:
                n.senden(alarm)
            except Exception as e:
                logger.error(f"{type(n).__name__} Fehler: {e}")
```

---

## 4. Fehlerbehandlung & Retries: EmailNotifier (Python)

**Datei (Auszug):** `backend/app/alarm_engine.py`

<!-- *Begründung für die Auswahl: Zeigt fortgeschrittene Programmierkonzepte 
wie saubere Fehlerbehandlung (Try-Catch), Retry-Mechanismen bei fehlschlagenden 
Netzwerkanfragen und die exakte Datenbank-Protokollierung von Sendestatus.* -->

```python
class EmailNotifier:
    def senden(self, alarm: Alarm) -> bool:
        if not self.enabled:
            return True

        # Email in DB speichern (Status: ausstehend)
        email_id = datenbank.alarm_email_speichern(
            alarm_id=alarm.id,
            empfaenger=self.empfaenger,
            subject=f"⚠️ Serverraum Alarm: {alarm.alarm_typ}",
            body=f"{alarm.nachricht}\nSensor: {alarm.sensor_id}\nWert: {alarm.wert}",
            sende_status='ausstehend'
        )

        fehler = None
        for versuch in range(3):
            try:
                success = self._sende(alarm)
                if success:
                    # Erfolgreich versendet -> DB Update
                    datenbank.alarm_email_aktualisieren(email_id, 'erfolgreich')
                    return True
            except Exception as e:
                fehler = e
                logger.warning(f"E-Mail Fehler (Versuch {versuch + 1}): {e}")
                if versuch < 2:
                    time.sleep(2) # Backoff vor nächstem Versuch

        # Final fehlgeschlagen -> Fehlerlog in DB speichern
        datenbank.alarm_email_aktualisieren(email_id, 'fehlgeschlagen', str(fehler))
        logger.error("E-Mail Alarm fehlgeschlagen")
        return False
```
