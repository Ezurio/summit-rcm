"""
Module to interact with network interfaces
"""

from syslog import LOG_ERR, syslog
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.services.network_service import NetworkService

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        BadRequestErrorResponseModel,
        InternalServerErrorResponseModel,
        NetworkInterfaceDriverInfoResponseModel,
        NetworkInterfaceResponseModel,
        NetworkInterfaceStatsResponseModel,
        NetworkInterfacesResponseModel,
        NotFoundErrorResponseModel,
        UnauthorizedErrorResponseModel,
    )
    from summit_rcm.rest_api.utils.spectree.tags import network_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    BadRequestErrorResponseModel = None
    InternalServerErrorResponseModel = None
    NetworkInterfaceDriverInfoResponseModel = None
    NetworkInterfaceResponseModel = None
    NetworkInterfaceStatsResponseModel = None
    NetworkInterfacesResponseModel = None
    NotFoundErrorResponseModel = None
    UnauthorizedErrorResponseModel = None
    network_tag = None


spec = SpectreeService()


class NetworkInterfacesResource(object):
    """
    Resource to handle queries and requests for all network interfaces
    """

    @spec.validate(
        resp=Response(
            HTTP_200=NetworkInterfacesResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=spec.security,
        tags=[network_tag],
    )
    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        Retrieve a list of network interfaces
        """
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

    @spec.validate(
        resp=Response(
            HTTP_200=NetworkInterfaceResponseModel,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=spec.security,
        tags=[network_tag],
    )
    async def on_get(
        self, _: falcon.asgi.Request, resp: falcon.asgi.Response, name: str
    ) -> None:
        """
        Retrieve details about a specific network interface
        """
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

    @spec.validate(
        resp=Response(
            HTTP_201=NetworkInterfaceResponseModel,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=spec.security,
        tags=[network_tag],
    )
    async def on_put(
        self, _: falcon.asgi.Request, resp: falcon.asgi.Response, name: str
    ) -> None:
        """Create virtual network interface (wlan1)"""
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

    @spec.validate(
        resp=Response(
            HTTP_200=None,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=spec.security,
        tags=[network_tag],
    )
    async def on_delete(
        self, _: falcon.asgi.Request, resp: falcon.asgi.Response, name: str
    ) -> None:
        """Remove virtual network interface (wlan1)"""
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

    @spec.validate(
        resp=Response(
            HTTP_200=NetworkInterfaceStatsResponseModel,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=spec.security,
        tags=[network_tag],
    )
    async def on_get(
        self, _: falcon.asgi.Request, resp: falcon.asgi.Response, name: str
    ) -> None:
        """Retrieve network interface statistics"""
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


class NetworkInterfaceDriverInfoResource(object):
    """
    Resource to handle queries and requests for network interface driver info
    """

    @spec.validate(
        resp=Response(
            HTTP_200=NetworkInterfaceDriverInfoResponseModel,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=spec.security,
        tags=[network_tag],
    )
    async def on_get(self, _, resp: falcon.asgi.Response, name: str) -> None:
        """Retrieve network interface driver info (country code)"""
        try:
            if not name:
                resp.status = falcon.HTTP_400
                return

            resp.media = await NetworkService.get_interface_driver_info(name=name)
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except FileNotFoundError:
            resp.status = falcon.HTTP_400
        except Exception as e:
            syslog(LOG_ERR, f"Unable to read interface driver info: {str(e)}")
            resp.status = falcon.HTTP_500
