"""
Module to handle network status info (legacy)
"""

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
        NetworkStatusResponseModelLegacy,
    )
    from summit_rcm.rest_api.utils.spectree.tags import network_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    NetworkStatusResponseModelLegacy = None
    network_tag = None


spec = SpectreeService()


class NetworkStatus:
    @spec.validate(
        resp=Response(
            HTTP_200=NetworkStatusResponseModelLegacy,
        ),
        tags=[network_tag],
        deprecated=True,
    )
    async def on_get(self, req, resp):
        """
        Retrieve network status info (legacy)
        """
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
