"""
Einfacher MQTT-Broker für lokale Tests
======================================

Startet einen lokalen MQTT-Broker auf Port 1883
mit hbmqtt (keine Root-Rechte nötig).

Verwendung:
    python mqtt_broker.py

@author Marc-Dennis Haberland
@date 17.04.2026
"""

import logging
import asyncio
from hbmqtt.broker import Broker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Startet den MQTT Broker"""
    broker = Broker({
        'listeners': {
            'default': {
                'type': 'tcp',
                'bind': '0.0.0.0:1883',
            }
        },
        'sys_interval': 0,
        'auth': {
            'allow-anonymous': True,
        }
    }, logger=logger)

    await broker.start()
    logger.info("MQTT Broker gestartet auf 0.0.0.0:1883")
    logger.info("Strg+C zum Beenden")

    try:
        await asyncio.Future()  # Läuft endlos
    except KeyboardInterrupt:
        pass
    finally:
        await broker.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
