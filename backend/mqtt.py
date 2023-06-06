import contextlib
import typing
import asyncio
import asyncio_mqtt
from aiohttp import web
from config import mqtt_hostname, logger, mqtt_port, mqtt_username, mqtt_password
from postgres import insert_bno055_data


async def subscribe_to_channels(client: asyncio_mqtt.Client) -> None:
    await client.subscribe("bno055")


async def handle_sensor_message(message: asyncio_mqtt.Message) -> None:
    buffer = typing.cast(bytes, message.payload)
    match f'{message.topic}':
        case 'bno055':
            await insert_bno055_data(buffer)

mqtt_client_connected: bool = False


def is_mqtt_healthy() -> bool:
    global mqtt_client_connected
    return mqtt_client_connected


async def mqtt_context(_: web.Application) -> typing.AsyncIterator[None]:
    task = asyncio.create_task(aiomqtt_coro())
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


async def aiomqtt_coro() -> None:
    global mqtt_client_connected
    reconnection_interval = 5
    while True:
        try:
            async with asyncio_mqtt.Client(hostname=mqtt_hostname,
                                           port=mqtt_port,
                                           password=mqtt_password,
                                           username=mqtt_username) as client:
                mqtt_client_connected = True
                logger.info(
                    f'Successfully connected to Mosquitto')
                await subscribe_to_channels(client)
                async with client.messages() as messages:
                    async for message in messages:
                        await handle_sensor_message(message)
        except asyncio_mqtt.MqttError:
            mqtt_client_connected = False
            logger.warning(
                f'Connection lost. Reconnecting in {reconnection_interval} seconds')
            await asyncio.sleep(reconnection_interval)
