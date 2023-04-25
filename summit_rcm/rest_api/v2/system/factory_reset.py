import asyncio
import os
import falcon
from summit_rcm.definition import MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE
from summit_rcm.services.system_service import SystemService, FACTORY_RESET_SCRIPT


class FactoryResetResource(object):
    """
    Resource to handle factory reset requests
    """

    async def on_put(self, req: falcon.Request, resp: falcon.Response) -> None:
        post_data = await req.get_media()
        initiate_factory_reset = post_data.get("initiateFactoryReset", None)
        auto_reboot = post_data.get("autoReboot", None)

        if initiate_factory_reset is None or auto_reboot is None:
            resp.status = falcon.HTTP_400
            return

        initiate_factory_reset = bool(initiate_factory_reset)
        auto_reboot = bool(auto_reboot)

        if not initiate_factory_reset:
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
            resp.media = {"initiateFactoryReset": False, "autoReboot": False}
            return

        if not os.path.exists(FACTORY_RESET_SCRIPT):
            resp.status = falcon.HTTP_500
            return

        if os.path.exists(MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE):
            resp.status = falcon.HTTP_500
            return

        returncode: int = await SystemService().initiate_factory_reset()

        if returncode != 0:
            resp.status = falcon.HTTP_500
            return

        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        resp.media = {
            "initiateFactoryReset": initiate_factory_reset,
            "autoReboot": auto_reboot,
        }

        if auto_reboot:
            asyncio.ensure_future(SystemService().set_power_state("reboot"))
