from syslog import LOG_ERR, syslog
import falcon
from summit_rcm.services.network_service import NetworkService
from summit_rcm.settings import ServerConfig


class NetworkInterfacesResource(object):
    """
    Resource to handle queries and requests for all network interfaces
    """

    async def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            resp.media = await NetworkService.get_all_interfaces()
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as e:
            syslog(
                LOG_ERR,
                f"Unable to retrieve list of network interface: {str(e)}",
            )
            resp.status = falcon.HTTP_500


class NetworkInterfaceResource(object):
    """
    Resource to handle queries and requests for a specific network interface
    """

    async def on_get(
        self, req: falcon.Request, resp: falcon.Response, name: str
    ) -> None:
        try:
            if not name:
                resp.status = falcon.HTTP_400
                return

            unmanaged_devices = (
                ServerConfig()
                .get_parser()
                .get("summit-rcm", "unmanaged_hardware_devices", fallback="")
                .split()
            )

            if name in unmanaged_devices:
                resp.status = falcon.HTTP_400
                return

            result = await NetworkService.get_interface_status(
                target_interface_name=name, is_legacy=False
            )

            if len(result) == 0:
                resp.status = falcon.HTTP_400
                return

            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
            resp.media = result
        except Exception as e:
            syslog(
                LOG_ERR,
                f"Unable to retrieve detailed network interface configuration: {str(e)}",
            )
            resp.status = falcon.HTTP_500

    async def on_put(
        self, req: falcon.Request, resp: falcon.Response, name: str
    ) -> None:
        try:
            # The only supported interface name is currently 'wlan1' and the only supported
            # interface type is STA/managed (so no need to require this in the request)
            if not name or name != "wlan1":
                resp.status = falcon.HTTP_400
                return

            # Check if the virtual interface already exists
            if name in await NetworkService.get_all_interfaces():
                resp.status = falcon.HTTP_400
                return

            if not await NetworkService.add_virtual_interface():
                resp.status = falcon.HTTP_500
                return

            # The interface creation was successful, so now return the current status properties for
            # it
            result = await NetworkService.get_interface_status(
                target_interface_name="wlan1", is_legacy=False
            )

            if len(result) == 0:
                resp.status = falcon.HTTP_500
                return

            resp.status = falcon.HTTP_201
            resp.content_type = falcon.MEDIA_JSON
            resp.media = result
        except Exception as e:
            syslog(
                LOG_ERR,
                f"Unable to add virtual network interface: {str(e)}",
            )
            resp.status = falcon.HTTP_500

    async def on_delete(
        self, req: falcon.Request, resp: falcon.Response, name: str
    ) -> None:
        try:
            # The only supported interface name is currently 'wlan1' and the only supported
            # interface type is STA/managed (so no need to require this in the request)
            if not name or name != "wlan1":
                resp.status = falcon.HTTP_400
                return

            # Check that the virtual interface exists
            if name not in await NetworkService.get_all_interfaces():
                resp.status = falcon.HTTP_404
                return

            if not await NetworkService.remove_virtual_interface():
                resp.status = falcon.HTTP_500
                return

            resp.status = falcon.HTTP_200
        except Exception as e:
            syslog(
                LOG_ERR,
                f"Unable to remove network interface: {str(e)}",
            )
            resp.status = falcon.HTTP_500


class NetworkInterfaceStatsResource(object):
    """
    Resource to handle queries and requests for network interface statistics
    """

    async def on_get(
        self, req: falcon.Request, resp: falcon.Response, name: str
    ) -> None:
        try:
            if not name:
                resp.status = falcon.HTTP_400
                return

            (success, stats) = await NetworkService.get_interface_statistics(
                target_interface_name=name, is_legacy=False
            )

            if not success:
                resp.status = falcon.HTTP_500
                return

            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
            resp.media = stats
        except Exception as e:
            syslog(
                LOG_ERR,
                f"Unable to retrieve list of network interface: {str(e)}",
            )
            resp.status = falcon.HTTP_500
