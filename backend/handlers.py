from datetime import datetime
from aiohttp import web
from mqtt import is_mqtt_healthy
from postgres import is_postgres_healthy, get_bno055_data
from config import logger


async def handle_bno055(req: web.Request) -> web.Response:
    ms_since_epoch = req.query.get("ms_since_epoch")
    timestamp = datetime.fromtimestamp(float(datetime.now().strftime("%s"))
                                       if ms_since_epoch is None
                                       else float(ms_since_epoch) / 1000)
    _timestamp, _sensor, _measurement, _value,  = await get_bno055_data(timestamp)
    result = dict(_timestamp=int(float(_timestamp.strftime('%s')) * 1000), _sensor=_sensor,
                  _measurement=_measurement, _value=_value)
    return web.json_response(result)


async def handle_root(_: web.Request) -> web.Response:
    healthy = is_mqtt_healthy() and await is_postgres_healthy()
    return web.json_response(dict(healthy=healthy))
