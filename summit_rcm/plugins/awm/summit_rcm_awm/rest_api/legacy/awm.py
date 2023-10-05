"""
Module to support configuration of AWM for legacy routes.
"""

import falcon
from summit_rcm import definition
from summit_rcm_awm.services.awm_config_service import AWMConfigService


class AWMResourceLegacy:
    """
    Resource to expose AWM configuration
    """

    async def on_get(self, req, resp):
        """
        GET handler for the /awm endpoint
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON

        # Infinite geo-location checks by default
        result = {
            "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "AWM configuration only supported in LITE mode",
            "geolocation_scanning_enable": 1,
        }

        try:
            scan_attempts = AWMConfigService().get_scan_attempts()
        except Exception:
            resp.media = result
            return

        result["geolocation_scanning_enable"] = scan_attempts
        result["InfoMsg"] = ""
        resp.media = result

    async def on_put(self, req, resp):
        """
        PUT handler for the /awm endpoint
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON

        # Enable/disable geolocation scanning
        # 0: disable geolocation scanning
        # others: enable geolocation scanning
        result = {
            "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "AWM's geolocation scanning configuration only supported in LITE mode",
            "geolocation_scanning_enable": 1,
        }

        if not AWMConfigService.get_lite_mode_enabled():
            resp.media = result
            return

        # prep for next error condition
        result["InfoMsg"] = "No writable configuration file found"

        put_data = await req.get_media()
        geolocation_scanning_enable = put_data.get("geolocation_scanning_enable", 0)

        try:
            AWMConfigService().set_scan_attempts(geolocation_scanning_enable)
        except Exception:
            resp.media = result
            return

        result["geolocation_scanning_enable"] = geolocation_scanning_enable
        result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        result["InfoMsg"] = ""
        resp.media = result
