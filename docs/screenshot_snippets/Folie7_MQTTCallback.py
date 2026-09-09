"""
@file Folie7_MQTTCallback.py
MQTT Message Callback - empfängt Sensordaten

Wichtig fuer die Dokumentation:
Dieses Snippet nutzt ein zweistufiges Basis-Topic.

Topic-Schema:
    serverraum/sensor/<sensor_id>/<msg_typ>

Index-Mapping nach split("/"):
    teile[0] = "serverraum"
    teile[1] = "sensor"
    teile[2] = <sensor_id>
    teile[3] = <msg_typ> (optional, Default: "data")

Sprechtext (Praesentation):
    "Unser MQTT-Basis-Topic ist zweistufig: serverraum/sensor.
    Deshalb liegt die sensor_id nach split('/') an Index 2;
    Index 3 ist optional der Nachrichtentyp wie data, alarm oder status."
"""

def _on_message(self, client, userdata, msg):
    """Verarbeitet eingehende MQTT-Nachrichten"""
    try:
        topic = msg.topic
        daten = json.loads(msg.payload.decode("utf-8"))

        # Topic parsen: serverraum/sensor/<sensor_id>/<msg_typ>
        teile = topic.split("/")
        sensor_id = teile[2]
        msg_typ = teile[3] if len(teile) > 3 else "data"

        # Routing nach Nachrichtentyp
        if msg_typ == "alarm":
            self._verarbeite_alarm(sensor_id, daten)
        elif msg_typ == "status":
            logger.info(f"Status: {daten.get('status')}")
        else:
            self._verarbeite_daten(sensor_id, daten)

    except Exception as e:
        logger.error(f"Message Fehler: {e}")
