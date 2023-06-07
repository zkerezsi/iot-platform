import contextlib
import typing
import asyncio
import aiopg
import asyncio_mqtt
from aiohttp import web
from config import mqtt_hostname, logger, mqtt_port, mqtt_username, mqtt_password
from postgres import insert_bno055_data


async def mqtt_context(app: web.Application) -> typing.AsyncIterator[None]:
    task = asyncio.create_task(aiomqtt_coro(app))
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


async def aiomqtt_coro(app: web.Application) -> None:
    pool: aiopg.Pool = app["pool"]
    app["mqtt_healthy"] = False
    reconnection_interval = 5
    while True:
        try:
            async with asyncio_mqtt.Client(hostname=mqtt_hostname,
                                           port=mqtt_port,
                                           password=mqtt_password,
                                           username=mqtt_username) as client:
                await client.subscribe("bno055")
                app["mqtt_healthy"] = True
                logger.info(
                    f'Successfully connected to Mosquitto')
                async with client.messages() as messages:
                    async for message in messages:
                        buffer = typing.cast(bytes, message.payload)
                        match f'{message.topic}':
                            case 'bno055':
                                await insert_bno055_data(pool, buffer)
        except asyncio_mqtt.MqttError:
            app["mqtt_healthy"] = False
            logger.warning(
                f'Connection lost. Reconnecting in {reconnection_interval} seconds')
            await asyncio.sleep(reconnection_interval)
