"""
Module to interact with Wi-Fi settings
"""

from syslog import LOG_ERR, syslog
import falcon.asgi
from summit_rcm.services.network_service import NetworkService

try:
    from summit_rcm.radio_siso_mode.radio_siso_mode_service import RadioSISOModeService
except ImportError:
    RadioSISOModeService = None
try:
    from summit_rcm.awm.awm_config_service import AWMConfigService
except ImportError:
    AWMConfigService = None


class WiFiResource(object):
    """
    Resource to handle queries and requests for Wi-Fi sesttings
    """

    async def get_current_settings(self) -> dict:
        """Retrieve a dictionary of the current Wi-Fi settings"""
        result = {}
        if RadioSISOModeService:
            try:
                result["sisoMode"] = RadioSISOModeService.get_current_siso_mode()
            except Exception as exception:
                # Default to -1 (system default) if there's an exception
                syslog(f"Unable to read SISO mode parameter: {str(exception)}")
                result["sisoMode"] = -1

        if AWMConfigService:
            try:
                result[
                    "geolocationScanningEnabled"
                ] = AWMConfigService().get_scan_attempts()
            except Exception as exception:
                # Default to 1 (enabled) if there's an exception
                syslog(f"Unable to read AWM configuration: {str(exception)}")
                result["geolocationScanningEnabled"] = 1

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
            if RadioSISOModeService:
                try:
                    siso_mode = int(put_data.get("sisoMode", None))
                    if siso_mode is None:
                        raise Exception("Invalid parameter")
                except Exception:
                    resp.status = falcon.HTTP_400
                    return
            else:
                siso_mode = None

            if AWMConfigService and AWMConfigService.get_lite_mode_enabled():
                try:
                    geolocation_scanning_enable = int(
                        put_data.get("geolocationScanningEnabled", 0)
                    )
                except Exception:
                    resp.status = falcon.HTTP_400
                    return
            else:
                geolocation_scanning_enable = None

            # We only need to check for 'software' enablement here, because that's all we can
            # control - ignore 'hardware'.
            wifi_radio_software_enabled = bool(
                put_data.get("wifiRadioSoftwareEnabled", None)
            )
            if wifi_radio_software_enabled is None:
                resp.status = falcon.HTTP_400
                return

            # Handle new inputs
            if (
                siso_mode is not None
                and siso_mode != RadioSISOModeService.get_current_siso_mode()
            ):
                try:
                    RadioSISOModeService.set_siso_mode(siso_mode)
                except Exception as exception:
                    syslog(f"Unable to configure SISO mode parameter: {str(exception)}")
                    resp.status = falcon.HTTP_500
                    return

            if geolocation_scanning_enable is not None:
                try:
                    AWMConfigService().set_scan_attempts(geolocation_scanning_enable)
                except Exception as exception:
                    syslog(f"Unable to configure AWM: {str(exception)}")
                    resp.status = falcon.HTTP_500
                    return

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
