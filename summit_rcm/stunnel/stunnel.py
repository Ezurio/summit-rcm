from syslog import LOG_ERR, syslog
import falcon
from ..systemd_unit import SystemdUnit
from ..definition import (
    SUMMIT_RCM_ERRORS,
)

STUNNEL_SERVICE_FILE = "stunnel.service"
STUNNEL_CONF_FILE = "/etc/stunnel/stunnel.conf"
STUNNEL_CONF_FIPS_ENABLED = "fips = yes"


class Stunnel(SystemdUnit):
    def __init__(self) -> None:
        super().__init__(STUNNEL_SERVICE_FILE)

    @staticmethod
    def configure_fips(enabled: bool):
        """
        Update the stunnel configuration file to enable/disable FIPS support according to the given
        parameter (enabled).
        """
        new_content = []
        with open(STUNNEL_CONF_FILE, "r") as stunnel_conf_file:
            for line in stunnel_conf_file.readlines():
                if STUNNEL_CONF_FIPS_ENABLED in line:
                    # Found the target line
                    new_content.append(
                        f"{'' if enabled else ';'}{STUNNEL_CONF_FIPS_ENABLED}\n"
                    )
                else:
                    new_content.append(line)
        with open(STUNNEL_CONF_FILE, "w") as stunnel_conf_file:
            stunnel_conf_file.writelines(new_content)

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Could not retrieve stunnel state",
            "state": "unknown",
        }

        try:
            result["state"] = await self.get_active_state()
            if result["state"] != "unknown":
                result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
                result["InfoMsg"] = ""
        except Exception as e:
            syslog(LOG_ERR, f"Could not retrieve stunnel state: {str(e)}")

        resp.media = result

    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Could not set stunnel state",
        }

        try:
            valid_states = ["active", "inactive"]

            post_data = await req.get_media()
            requested_state = post_data.get("state", None)
            if not requested_state:
                result["InfoMsg"] = f"Invalid state; valid states: {valid_states}"
                resp.media = result
                return
            if requested_state not in valid_states:
                result[
                    "InfoMsg"
                ] = f"Invalid state: {requested_state}; valid states: {valid_states}"
                resp.media = result
                return

            # Read the current 'ActiveState' of the stunnel service
            current_state = await self.get_active_state()

            if str(requested_state) == current_state:
                # No change needed
                result["InfoMsg"] = f"stunnel already {current_state}"
                result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            else:
                if requested_state == "active":
                    # Activate service
                    if await self.activate():
                        result["InfoMsg"] = "stunnel activated"
                        result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
                elif requested_state == "inactive":
                    # Deactivate service
                    if await self.deactivate():
                        result["InfoMsg"] = "stunnel deactivated"
                        result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as e:
            syslog(LOG_ERR, f"Could not set stunnel state: {str(e)}")
            result = {
                "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
                "InfoMsg": "Could not set stunnel state",
            }

        resp.media = result
