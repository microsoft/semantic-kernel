# Copyright (c) Microsoft. All rights reserved.

import logging
import os

from aiohttp import web
from aiohttp.web import Request, Response
from bot import bot
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Endpoint for processing messages
async def messages(req: Request):
    """
    Endpoint for processing messages with the Skill Bot.
    """
    logger.info("Received a message.")
    body = await req.json()
    logger.info("Request body: %s", body)

    # Process the incoming request
    # NOTE in the context of Skills, we MUST return the response to the Copilot Studio as the response to the request
    # In other channel (ex. Teams), this would not be required, and activities would be sent to the Bot Framework
    return await bot.process(req)


async def copilot_manifest(req: Request):
    # load manifest from file and interpolate with env vars
    with open("copilot-studio.manifest.json") as f:
        manifest = f.read()

        # Get container app current ingress fqdn
        # See https://learn.microsoft.com/en-us/azure/container-apps/environment-variables?tabs=portal
        fqdn = f"https://{os.getenv('CONTAINER_APP_NAME')}.{os.getenv('CONTAINER_APP_ENV_DNS_SUFFIX')}/api/messages"

        manifest = manifest.replace("__botEndpoint", fqdn).replace("__botAppId", config.APP_ID)

    return Response(
        text=manifest,
        content_type="application/json",
    )


APP = web.Application()
APP.router.add_post("/api/messages", messages)
APP.router.add_get("/manifest", copilot_manifest)

if __name__ == "__main__":
    try:
        web.run_app(APP, host=config.HOST, port=config.PORT)
    except Exception as error:
        raise error
