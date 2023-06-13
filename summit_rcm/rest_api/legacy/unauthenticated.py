from syslog import syslog, LOG_ERR

import falcon

from summit_rcm.definition import SUMMIT_RCM_ERRORS
from summit_rcm.settings import ServerConfig, SystemSettingsManage


class AllowUnauthenticatedResetReboot:
    def __init__(self) -> None:
        self._allowed: bool = (
            ServerConfig()
            .get_parser()
            .getboolean(
                section="summit-rcm",
                option="enable_allow_unauthenticated_reboot_reset",
                fallback=False,
            )
        )

    @property
    def allow_unauthenticated_reset_reboot(self) -> bool:
        return self._allowed and SystemSettingsManage.getBool(
            "AllowUnauthenticatedRebootReset", False
        )

    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Cannot set allow unauthenticated reset reboot",
        }

        try:
            if ServerConfig().get_parser().getboolean(
                section="summit-rcm",
                option="enable_allow_unauthenticated_reboot_reset",
                fallback=False,
            ) and SystemSettingsManage.update_persistent(
                "AllowUnauthenticatedRebootReset", str(True)
            ):
                result["InfoMsg"] = ""
                result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as e:
            result[
                "SDCERR"
            ] = f"AllowUnauthenticatedRebootReset cannot be set: {str(e)}"
            syslog(
                LOG_ERR, f"AllowUnauthenticatedRebootReset" f" cannot be set: {str(e)}"
            )
        resp.media = result

    async def on_delete(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Cannot clear allow unauthenticated reset reboot",
        }

        try:
            if SystemSettingsManage.update_persistent(
                "AllowUnauthenticatedRebootReset", str(False)
            ):
                result["InfoMsg"] = ""
                result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as e:
            result[
                "SDCERR"
            ] = f"AllowUnauthenticatedRebootReset cannot be set: {str(e)}"
            syslog(
                LOG_ERR, f"AllowUnauthenticatedRebootReset" f" cannot be set: {str(e)}"
            )
        resp.media = result

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Cannot read allow unauthenticated reset reboot",
        }

        try:
            result[
                "allowUnauthenticatedRebootReset"
            ] = self.allow_unauthenticated_reset_reboot
            result["InfoMsg"] = ""
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as e:
            result[
                "SDCERR"
            ] = f"AllowUnauthenticatedRebootReset cannot be read: {str(e)}"
            syslog(
                LOG_ERR, f"AllowUnauthenticatedRebootReset" f" cannot be read: {str(e)}"
            )
        resp.media = result
