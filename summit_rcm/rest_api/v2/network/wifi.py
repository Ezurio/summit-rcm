"""
Module to interact with Wi-Fi settings
"""

from syslog import LOG_ERR, syslog
import falcon.asgi
from summit_rcm.services.network_service import NetworkService


class WiFiResource(object):
    """
    Resource to handle queries and requests for Wi-Fi settings
    """

    async def get_current_settings(self) -> dict:
        """Retrieve a dictionary of the current Wi-Fi settings"""
        result = {}

        try:
            result[
                "wifiRadioSoftwareEnabled"
            ] = await NetworkService.get_wireless_enabled()
            result[
                "wifiRadioHardwareEnabled"
            ] = await NetworkService.get_wireless_hardware_enabled()
        except Exception as exception:
            syslog(f"Unable to read Wi-Fi enabled properties: {str(exception)}")
            result["wifiRadioSoftwareEnabled"] = False
            result["wifiRadioHardwareEnabled"] = False

        return result

    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        GET handler for the /network/wifi endpoint
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

    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        PUT handler for the /network/wifi endpoint
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
