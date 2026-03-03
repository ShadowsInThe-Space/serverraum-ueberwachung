# Klassendiagramm – Sensor-Polymorphie

## Übersicht

Das Klassendiagramm zeigt die objektorientierte Struktur der ESP32-Firmware mit Polymorphie zur Sensor-Abstraktion.

```mermaid
classDiagram
    class Sensor {
        <<abstract>>
        -int gpioPin
        -String sensorId
        -bool isActive
        +Sensor(int pin, String id)
        +init() bool
        +read() SensorData
        +getSensorType() String
    }

    class SensorData {
        +String sensorType
        +float value
        +String unit
        +DateTime timestamp
        +bool hasError
        +String errorMessage
    }

    class DHT22Sensor {
        -DHT* dht
        +DHT22Sensor(int pin, String id)
        +init() bool
        +read() SensorData
    }

    class DS18B20Sensor {
        -OneWire* oneWire
        -DallasTemperature* sensors
        +DS18B20Sensor(int pin, String id)
        +init() bool
        +read() SensorData
    }

    class MQ2Sensor {
        -int adcPin
        -int roCleanAir
        +MQ2Sensor(int pin, String id)
        +init() bool
        +read() SensorData
        -calculatePPM(float rsRoRatio) float
    }

    class MQ135Sensor {
        -int adcPin
        -float loadResistor
        +MQ135Sensor(int pin, String id)
        +init() bool
        +read() SensorData
        -calculatePPM(float voltage) float
    }

    class PIRSensor {
        -int pirPin
        -bool lastMotion
        -unsigned long lastMotionTime
        +PIRSensor(int pin, String id)
        +init() bool
        +read() SensorData
        -debounceMotion() bool
    }

    class SensorRegistry {
        -Sensor* sensors[10]
        -int sensorCount
        +registerSensor(Sensor* sensor) bool
        +removeSensor(String sensorId) bool
        +getSensor(String sensorId) Sensor*
        +readAll() SensorData[]
        +initAll() bool
    }

    class MQTTSender {
        -PubSubClient mqttClient
        -String deviceId
        -String topicPrefix
        +MQTTSender(WiFiClient& client, String broker, String deviceId)
        +connect() bool
        +publish(SensorData data) bool
        +publishBatch(SensorData[] data, int count) bool
        +isConnected() bool
    }

    Sensor <|-- DHT22Sensor
    Sensor <|-- DS18B20Sensor
    Sensor <|-- MQ2Sensor
    Sensor <|-- MQ135Sensor
    Sensor <|-- PIRSensor

    Sensor --> SensorData
    SensorRegistry --> Sensor
    MQTTSender --> SensorData
```

## Erklärung der Klassen

### Sensor (abstrakte Basisklasse)
Die abstrakte Basisklasse `Sensor` definiert das gemeinsame Interface für alle Sensoren:
- `init()`: Initialisierung des Sensors
- `read()`: Messwert lesen
- `getSensorType()`: Sensortyp abfragen

### Konkrete Sensor-Klassen
Jeder Sensor erbt von `Sensor` und implementiert seine eigene Logik:
- **DHT22Sensor**: Temperatur und Luftfeuchtigkeit (digital)
- **DS18B20Sensor**: Temperatur (OneWire)
- **MQ2Sensor**: Rauchgas (analog)
- **MQ135Sensor**: Luftqualität (analog)
- **PIRSensor**: Bewegung (digital)

### SensorRegistry
Verwaltet alle Sensoren und ermöglicht:
- Registrierung/Entfernung von Sensoren
- Globales Auslesen aller Sensoren

### MQTTSender
Kümmert sich um die MQTT-Kommunikation:
- Verbindungsaufbau zum Broker
- Publishen von Sensordaten

## Vorteile der Polymorphie

1. **Wartbarkeit**: Neue Sensoren können einfach hinzugefügt werden
2. **Erweiterbarkeit**: Änderungen an einem Sensor beeinflussen nicht andere
3. **Testbarkeit**: Jeder Sensor kann einzeln getestet werden
4. **Lesbarkeit**: Klare Struktur und einheitliches Interface
