import aiohttp_cors
from aiohttp import web
from handlers import handle_bno055, handle_root
from config import logger, port
from mqtt import mqtt_context
from postgres import postgres_context


if __name__ == '__main__':
    logger.info(f"Starting backend service on http://localhost:{port}")
    app = web.Application()
    app.cleanup_ctx.append(postgres_context)
    app.cleanup_ctx.append(mqtt_context)
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*"
        )
    })
    app.add_routes([
        web.get('/', handle_root),
        web.get('/bno055', handle_bno055)
    ])
    for route in list(app.router.routes()):
        cors.add(route)
    web.run_app(app, port=port)
