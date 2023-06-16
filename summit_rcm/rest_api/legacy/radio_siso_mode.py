"""
Module to support configuration of the radio's SISO mode parameter for legacy routes.
"""

import falcon
from summit_rcm import definition
from summit_rcm.radio_siso_mode.radio_siso_mode_service import RadioSISOModeService


class RadioSISOModeResourceLegacy:
    """
    Resource to expose SISO mode configuration
    """

    async def on_get(self, req, resp):
        """
        GET handler for the /radioSISOMode endpoint
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": definition.SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS"),
            "InfoMsg": "",
            "SISO_mode": -1,
        }
        try:
            result["SISO_mode"] = RadioSISOModeService.get_current_siso_mode()
        except Exception as exception:
            result["InfoMsg"] = f"Unable to read SISO_mode parameter - {str(exception)}"
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS.get("SDCERR_FAIL")

        resp.media = result

    async def on_put(self, req, resp):
        """
        PUT handler for the /radioSISOMode endpoint
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": definition.SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS"),
            "InfoMsg": "",
            "SISO_mode": -1,
        }
        try:
            siso_mode = req.params.get("SISO_mode", None)
            if siso_mode is None:
                raise Exception("invalid parameter value")
            RadioSISOModeService.set_siso_mode(int(siso_mode))
            result["SISO_mode"] = RadioSISOModeService.get_current_siso_mode()
        except Exception as exception:
            try:
                # If we hit an exception for some reason, try to retrieve the current SISO mode
                # to report it back to the user if we can
                result["SISO_mode"] = RadioSISOModeService.get_current_siso_mode()
            except Exception:
                pass
            result["InfoMsg"] = f"Unable to set SISO_mode parameter - {str(exception)}"
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS.get("SDCERR_FAIL")

        resp.media = result
