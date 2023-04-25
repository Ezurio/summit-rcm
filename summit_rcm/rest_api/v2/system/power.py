import falcon
from summit_rcm.services.system_service import SystemService, VALID_POWER_STATES


class PowerResource(object):
    """
    Resource to handle power state queries and requests
    """

    async def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        resp.media = {"state": SystemService().power_state}

    async def on_put(self, req: falcon.Request, resp: falcon.Response) -> None:
        post_data = await req.get_media()
        desired_state = str(post_data.get("state", ""))
        if desired_state == "" or desired_state not in VALID_POWER_STATES:
            resp.status = falcon.HTTP_400
            return

        await SystemService().set_power_state(desired_state)

        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        resp.media = {"state": SystemService().power_state}
