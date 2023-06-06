import json
import struct
import typing
import aiopg
from aiohttp import web
from datetime import datetime
from config import logger, postgres_db, postgres_host, postgres_password, postgres_port, postgres_user


class Bno055Value(typing.TypedDict):
    frequency: list[float]
    x_axis: list[float]
    y_axis: list[float]
    z_axis: list[float]


pool: typing.Optional[aiopg.Pool]


async def is_postgres_healthy():
    global pool
    if pool is None:
        return False
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                value, = typing.cast(tuple[int], await cur.fetchone())
                return value == 1
    except:
        return False


async def postgres_context(_: web.Application) -> typing.AsyncIterator[None]:
    async with aiopg.create_pool(user=postgres_user,
                                 database=postgres_db,
                                 host=postgres_host,
                                 port=postgres_port,
                                 password=postgres_password) as p:
        async with p.acquire() as conn:
            async with conn.cursor() as cur:
                create_table = '''
                CREATE TABLE IF NOT EXISTS sensor_data(
                    _timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    _sensor VARCHAR NOT NULL,
                    _measurement VARCHAR NOT NULL,
                    _value JSONB NOT NULL
                );
                '''
                await cur.execute(create_table)
                create_index = '''
                CREATE INDEX IF NOT EXISTS _timestamp_index ON sensor_data USING BRIN(_timestamp);
                '''
                await cur.execute(create_index)
        global pool
        pool = p
        yield


async def insert_bno055_data(raw_bytes: bytes) -> None:
    if len(raw_bytes) != 1024:
        logger.error(
            'Invalid number of bytes received from bno055: should be 1024')
        return
    values = typing.cast(tuple[float], struct.unpack('256f', raw_bytes))
    frequency: list[float] = list()
    x_axis: list[float] = list()
    y_axis: list[float] = list()
    z_axis: list[float] = list()
    for index, value in enumerate(values):
        match index % 4:
            case 0:
                frequency.append(value)
            case 1:
                x_axis.append(value)
            case 2:
                y_axis.append(value)
            case 3:
                z_axis.append(value)
    _sensor = "bno055"
    _measurement = "vibration_fxyz"
    _value = json.dumps(dict(frequency=frequency,
                             x_axis=x_axis,
                             y_axis=y_axis,
                             z_axis=z_axis))
    global pool
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            command = '''
            INSERT INTO sensor_data (_sensor, _measurement, _value) VALUES (%s, %s, %s);
            '''
            await cur.execute(command, (_sensor, _measurement, _value))


async def get_bno055_data(timestamp: datetime):
    global pool
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            command = '''
            SELECT s._timestamp, s._sensor, s._measurement, s._value
            FROM sensor_data s
            WHERE s._timestamp <= %s
                AND s._sensor = 'bno055'
                AND s._measurement = 'vibration_fxyz'
            ORDER BY s._timestamp DESC
            LIMIT 1;
            '''
            await cur.execute(command, (timestamp,))
            return typing.cast(tuple[datetime, str, str, Bno055Value], await cur.fetchone())
