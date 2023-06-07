from datetime import datetime
from aiohttp import web
import aiopg
from postgres import is_postgres_healthy, get_bno055_data


async def handle_bno055(req: web.Request) -> web.Response:
    pool: aiopg.Pool = req.app["pool"]
    ms_since_epoch = req.query.get("ms_since_epoch")
    timestamp = datetime.fromtimestamp(float(datetime.now().strftime("%s"))
                                       if ms_since_epoch is None
                                       else float(ms_since_epoch) / 1000)
    _timestamp, _sensor, _measurement, _value, = await get_bno055_data(pool, timestamp)
    return web.json_response({
        "_timestamp": int(float(_timestamp.strftime('%s')) * 1000),
        "_sensor": _sensor,
        "_measurement": _measurement,
        "_value": _value
    })


async def handle_root(req: web.Request) -> web.Response:
    pool: aiopg.Pool = req.app["pool"]
    mqtt_healthy: bool = req.app["mqtt_healthy"]
    return web.json_response({
        "healthy": mqtt_healthy and await is_postgres_healthy(pool)
    })
