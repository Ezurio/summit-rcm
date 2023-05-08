import falcon
from summit_rcm.services.network_service import NetworkService
from summit_rcm.settings import ServerConfig


class NetworkStatus:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 0, "InfoMsg": ""}

        try:
            result["status"] = await NetworkService().get_status(is_legacy=True)

            unmanaged_devices = (
                ServerConfig()
                .get_parser()
                .get("summit-rcm", "unmanaged_hardware_devices", fallback="")
                .split()
            )
            for dev in unmanaged_devices:
                if dev in result["status"]:
                    del result["status"][dev]
            result["devices"] = len(result["status"])
            resp.media = result
        except Exception as e:
            result["InfoMsg"] = f"Could not read network status - {str(e)}"
            result["SDCERR"] = 1
            resp.media = result
