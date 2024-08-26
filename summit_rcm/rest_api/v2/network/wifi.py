#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to interact with Wi-Fi settings
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
        InternalServerErrorResponseModel,
        UnauthorizedErrorResponseModel,
        WiFiEnableInfoResponseModel,
    )
    from summit_rcm.rest_api.utils.spectree.tags import network_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    InternalServerErrorResponseModel = None
    UnauthorizedErrorResponseModel = None
    WiFiEnableInfoResponseModel = None
    network_tag = None


spec = SpectreeService()


class WiFiResource(object):
    """
    Resource to handle queries and requests for Wi-Fi settings
    """

    async def get_current_settings(self) -> dict:
        """Retrieve a dictionary of the current Wi-Fi settings"""
        result = {}

        try:
            result["wifiRadioSoftwareEnabled"] = (
                await NetworkService.get_wireless_enabled()
            )
            result["wifiRadioHardwareEnabled"] = (
                await NetworkService.get_wireless_hardware_enabled()
            )
        except Exception as exception:
            syslog(f"Unable to read Wi-Fi enabled properties: {str(exception)}")
            result["wifiRadioSoftwareEnabled"] = False
            result["wifiRadioHardwareEnabled"] = False

        return result

    @spec.validate(
        resp=Response(
            HTTP_200=WiFiEnableInfoResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=spec.security,
        tags=[network_tag],
    )
    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        Retrieve current Wi-Fi radio state
        """
        try:
            resp.media = await self.get_current_settings()
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to retrieve Wi-Fi settings: {str(exception)}",
            )
            resp.status = falcon.HTTP_500

    @spec.validate(
        json=WiFiEnableInfoResponseModel,
        resp=Response(
            HTTP_200=WiFiEnableInfoResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=spec.security,
        tags=[network_tag],
    )
    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        Enable/disable Wi-Fi radio
        """
        try:
            # Parse inputs
            put_data: dict = await req.get_media()

            # We only need to check for 'software' enablement here, because that's all we can
            # control - ignore 'hardware'.
            wifi_radio_software_enabled = bool(
                put_data.get("wifiRadioSoftwareEnabled", None)
            )
            if wifi_radio_software_enabled is None:
                resp.status = falcon.HTTP_400
                return

            # Handle new inputs
            try:
                if (
                    wifi_radio_software_enabled
                    != await NetworkService.get_wireless_enabled()
                ):
                    await NetworkService.set_wireless_enabled(
                        wifi_radio_software_enabled
                    )
            except Exception as exception:
                syslog(f"Unable to configure Wi-Fi enable/disable: {str(exception)}")
                resp.status = falcon.HTTP_500
                return

            # Prepare response
            resp.media = await self.get_current_settings()
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to configure Wi-Fi settings: {str(exception)}",
            )
            resp.status = falcon.HTTP_500
