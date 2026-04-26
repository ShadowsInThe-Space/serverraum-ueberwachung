"""
Mock-MQTT-Broker für lokale Tests
================================

Ein einfacher Mock-Broker der MQTT-Nachrichten empfängt und loggt.
Startet einen TCP-Server auf Port 1883 und nimmt Verbindungen an.

Verwendung:
    python mock_broker.py

@author Marc-Dennis Haberland
@date 17.04.2026
"""

import socket
import threading
import json
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PORT = 1883
BUFFER_SIZE = 4096


class MockMqttBroker:
    """Mock MQTT Broker für lokale Tests"""

    def __init__(self, port=1883):
        self.port = port
        self.running = False
        self.server_socket = None
        self.client_threads = []

    def start(self):
        """Startet den Mock-Broker"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(5)
        self.running = True

        logger.info(f"Mock-MQTT-Broker gestartet auf 0.0.0.0:{self.port}")
        logger.info("Drücke Strg+C zum Beenden")

        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                try:
                    client_socket, address = self.server_socket.accept()
                    logger.info(f"Verbindung von {address}")
                    thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    thread.start()
                except socket.timeout:
                    continue
            except Exception as e:
                if self.running:
                    logger.error(f"Server-Fehler: {e}")

    def handle_client(self, client_socket, address):
        """Behandelt eine Client-Verbindung"""
        try:
            while self.running:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break

                # Versuche MQTT-Nachricht zu parsen (vereinfacht)
                self.process_mqtt_data(data, client_socket, address)

        except Exception as e:
            logger.debug(f"Client {address} getrennt: {e}")
        finally:
            client_socket.close()

    def process_mqtt_data(self, data, client_socket, address):
        """Verarbeitet empfangene MQTT-Daten"""
        # MQTT Packet Type aus erstem Byte
        if len(data) > 0:
            packet_type = data[0] >> 4
            packet_names = {
                1: "CONNECT",
                2: "CONNACK",
                3: "PUBLISH",
                4: "PUBACK",
                5: "PUBREC",
                6: "PUBREL",
                7: "PUBCOMP",
                8: "SUBSCRIBE",
                9: "SUBACK",
                10: "UNSUBSCRIBE",
                11: "UNSUBACK",
                12: "PINGREQ",
                13: "PINGRESP",
                14: "DISCONNECT",
                15: "AUTH"
            }
            name = packet_names.get(packet_type, f"UNKNOWN({packet_type})")

            # Bei SUBSCRIBE loggen wir die Topics
            if packet_type == 8 and len(data) >= 5:
                try:
                    # Vereinfacht: Extrahiere Topic aus dem Packet
                    logger.info(f"Client {address} -> {name}")
                except Exception:
                    logger.info(f"Client {address} -> {name}")

            # Bei PUBLISH loggen wir die Daten
            elif packet_type == 3:
                try:
                    # MQ-2 Packet: fixed header(2) + variable header(2) + payload
                    if len(data) >= 5:
                        topic_len = (data[2] << 8) | data[3]
                        if len(data) >= 4 + topic_len:
                            topic = data[4:4+topic_len].decode('utf-8', errors='ignore')
                            payload_start = 4 + topic_len
                            payload_data = data[payload_start:].decode('utf-8', errors='ignore')

                            logger.info(f"PUBLISH: {topic}")
                            try:
                                json_data = json.loads(payload_data)
                                logger.info(f"  Payload: {json_data}")
                            except:
                                logger.info(f"  Raw: {payload_data[:100]}")
                except Exception as e:
                    logger.debug(f"Parse-Fehler: {e}")

    def stop(self):
        """Stoppt den Mock-Broker"""
        logger.info("Mock-Broker wird gestoppt...")
        self.running = False
        if self.server_socket:
            self.server_socket.close()


def main():
    """Hauptschleife"""
    broker = MockMqttBroker(PORT)

    try:
        broker.start()
    except KeyboardInterrupt:
        logger.info("Strg+C erkannt")
    finally:
        broker.stop()
        logger.info("Mock-Broker beendet.")


if __name__ == "__main__":
    main()
