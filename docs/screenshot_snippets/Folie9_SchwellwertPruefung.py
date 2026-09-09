"""
@file Folie9_SchwellwertPruefung.py
Alarm-Engine: Schwellwert-Prüfung und Alarm-Auslösung
"""

def pruefe_alarm(self, sensor_id: str, sensor_typ: str, wert: float):
    """Prüft Schwellwerte und erstellt Alarm"""

    # Temperatur prüfen
    if sensor_typ in ["DS18B20", "SHT31"]:
        if wert > config.alarm.temperatur_max:
            return Alarm(
                sensor_id, "TEMPERATUR_HOCH",
                f"Temperatur zu hoch: {wert:.1f}°C",
                wert, config.alarm.temperatur_max
            )
        if wert < config.alarm.temperatur_min:
            return Alarm(
                sensor_id, "TEMPERATUR_NIEDRIG",
                f"Temperatur zu niedrig: {wert:.1f}°C",
                wert, config.alarm.temperatur_min
            )

    # Rauchgas prüfen
    elif sensor_typ == "MQ2" and wert > config.alarm.rauchgas_max:
        return Alarm(
            sensor_id, "RAUCHGAS",
            f"Rauchgas: {wert:.0f} ppm",
            wert, config.alarm.rauchgas_max
        )

    return None


def alarm_ausloesen(self, alarm: Alarm):
    """Löst Alarm aus + Benachrichtigungen"""

    # Spam-Schutz prüfen
    if not self._spam.ist_erlaubt(f"{alarm.sensor_id}_{alarm.alarm_typ}"):
        return

    logger.warning(f"ALARM: {alarm.nachricht}")

    # DB speichern
    alarm.id = datenbank.alarm_speichern(...)

    # Alle Notifier (Email, LED, Buzzer)
    for n in self._notifier:
        n.senden(alarm)
