from syslog import LOG_ERR, syslog
import falcon
from summit_rcm.services.network_service import NetworkService
from summit_rcm.settings import ServerConfig


class NetworkStatusResource(object):
    """
    Resource to handle network status queries and requests
    """

    async def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON

            result = {}
            result["status"] = await NetworkService.get_status(is_legacy=False)

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
            syslog(LOG_ERR, f"Could not retrieve network status - {str(e)}")
            resp.status = falcon.HTTP_500
