"""Core hosts the jabfy-bus pipeline in process (MASTER_PLAN §2.1, Option A).

Every bus publication happens on the asyncio loop thread: paho callbacks are
handed back to the loop, so handlers never run concurrently.
"""

import asyncio
import json
import logging
from typing import Any

import paho.mqtt.client as paho
from jabfy_bus.adapters.zigbee2mqtt.adapter import Zigbee2MQTTAdapter
from jabfy_bus.audit.log import AuditLog
from jabfy_bus.core.bus import UniversalJsonBus
from jabfy_bus.core.registry import EntityRegistry
from jabfy_bus.execution.executor import ExecutionLayer
from jabfy_bus.verification.engine import VerificationEngine
from jabfy_bus.verification.policies import Policy

from app.schemas.simulation import SimulationContext

logger = logging.getLogger(__name__)


class BusRuntime:
    def __init__(
        self,
        policies: list[Policy],
        *,
        mqtt_broker: str = "",
        base_topic: str = "zigbee2mqtt",
    ) -> None:
        self.bus = UniversalJsonBus()
        self.audit = AuditLog()
        self.audit.attach(self.bus)
        self.registry = EntityRegistry()
        self.registry.attach(self.bus)
        self.z2m = Zigbee2MQTTAdapter(self.bus, base_topic=base_topic, name="core_z2m_adapter")
        self.z2m.start()
        self.verification = VerificationEngine(self.bus, policies=policies)
        self.verification.attach()
        self.execution = ExecutionLayer(self.bus, audit=self.audit)
        self.execution.attach()
        self.execution.register_transport("zigbee", self._mqtt_transport)
        self.execution.register_transport("mqtt", self._mqtt_transport)

        self.mqtt_broker = mqtt_broker
        self.base_topic = base_topic
        self._loop: asyncio.AbstractEventLoop | None = None
        self._client: paho.Client | None = None

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        if not self.mqtt_broker:
            logger.warning("JABFY_MQTT_BROKER is not set: the bus cannot reach any device")
            return
        host, _, port = self.mqtt_broker.rpartition(":")
        client = paho.Client(
            callback_api_version=paho.CallbackAPIVersion.VERSION2, client_id="jabfy-core-bus",
        )
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.connect_async(host or self.mqtt_broker, int(port or 1883))
        client.loop_start()
        self._client = client

    def stop(self) -> None:
        if self._client is not None:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None

    @property
    def connected(self) -> bool:
        return self._client is not None and self._client.is_connected()

    def register_inventory(self, context: SimulationContext) -> None:
        """Telemetry carries the room once the adapter knows each wire name."""
        prefix = self.base_topic + "/"
        for device in context.devices:
            if device.bus is not None and device.bus.topic.startswith(prefix):
                self.z2m.register_device(device.bus.topic[len(prefix):], location=device.room_id)

    def _on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        if reason_code == 0:
            client.subscribe(f"{self.base_topic}/#", qos=0)
            logger.info("Core bus connected to MQTT %s", self.mqtt_broker)
        else:
            logger.error("Core bus MQTT connection failed: %s", reason_code)

    def _on_message(self, client, userdata, message) -> None:
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._handle_mqtt, message.topic, message.payload)

    def _handle_mqtt(self, topic: str, payload: bytes) -> None:
        try:
            self.z2m.handle_mqtt(topic, payload)
        except Exception:
            logger.exception("error handling MQTT message on %s", topic)

    def _mqtt_transport(self, target: str, payload: Any) -> None:
        if not self.connected:
            raise ConnectionError("The MQTT broker is not connected.")
        body = payload if isinstance(payload, str) else json.dumps(payload)
        info = self._client.publish(target, body, qos=1, retain=False)
        if info.rc != paho.MQTT_ERR_SUCCESS:
            raise ConnectionError(f"MQTT publish failed: {paho.error_string(info.rc)}")
