from syslog import LOG_ERR, syslog
import falcon
from summit_rcm.services.log_forwarding_service import (
    VALID_STATES,
    ActivationFailedError,
    AlreadyActiveError,
    AlreadyInactiveError,
    DeactivationFailedError,
    LogForwardingService,
)
from summit_rcm.services.logs_service import (
    VALID_SUPPLICANT_DEBUG_LEVELS,
    JournalctlError,
    LogsService,
)
from summit_rcm.definition import SUMMIT_RCM_ERRORS


class LogData:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 0, "InfoMsg": ""}

        try:
            priority = int(req.params.get("priority", 7))
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Error parsing 'priority' parameter as an integer: {str(exception)}",
            )
            resp.media = {"SDCERR": 1, "InfoMsg": "Priority must be an int between 0-7"}
            return
        typ = req.params.get("type", "All")
        try:
            days = int(req.params.get("days", 1))
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Error parsing 'days' parameter as an integer: {str(exception)}",
            )
            resp.media = {"SDCERR": 1, "InfoMsg": "days must be an int"}
            return

        try:
            logs = LogsService.get_journal_log_data(
                log_type=typ, priority=priority, days=days
            )
            result["InfoMsg"] = f"type: {typ}; days: {days}; Priority: {priority}"
            result["count"] = len(logs)
            result["log"] = logs
            resp.media = result
        except JournalctlError as error:
            syslog(
                LOG_ERR,
                f"Could not read journal logs: {str(error.return_code)}, {str(error)}",
            )
            resp.media = {"SDCERR": 1, "InfoMsg": "Could not read journal logs"}
        except Exception as exception:
            syslog(LOG_ERR, f"Could not read journal logs: {str(exception)}")
            resp.media = {"SDCERR": 1, "InfoMsg": "Could not read journal logs"}


class LogForwarding:
    async def on_get(self, _, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Could not retrieve log forwarding state",
            "state": "unknown",
        }

        try:
            result["state"] = await LogForwardingService().get_active_state()
            if result["state"] != "unknown":
                result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
                result["InfoMsg"] = ""
        except Exception as exception:
            syslog(
                LOG_ERR, f"Could not retrieve log forwarding state: {str(exception)}"
            )

        resp.media = result

    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Could not set log forwarding state",
        }

        try:
            post_data = await req.get_media()
            requested_state = post_data.get("state", None)
            if not requested_state:
                result["InfoMsg"] = f"Invalid state; valid states: {VALID_STATES}"
                resp.media = result
                return
            if requested_state not in VALID_STATES:
                result[
                    "InfoMsg"
                ] = f"Invalid state: {requested_state}; valid states: {VALID_STATES}"
                resp.media = result
                return

            await LogForwardingService().set_state(requested_state)
        except AlreadyActiveError:
            result["InfoMsg"] = "Log forwarding already active"
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except AlreadyInactiveError:
            result["InfoMsg"] = "Log forwarding already inactive"
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except ActivationFailedError:
            result["InfoMsg"] = "could not activate log forwarding service"
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
        except DeactivationFailedError:
            result["InfoMsg"] = "could not deactivate log forwarding service"
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
        except Exception as exception:
            syslog(LOG_ERR, f"Could not set log forwarding state: {str(exception)}")
            result = {
                "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
                "InfoMsg": "Could not set log forwarding state",
            }

        resp.media = result


class LogSetting:
    async def on_post(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 1, "InfoMsg": ""}
        post_data = await req.get_media()

        if "suppDebugLevel" not in post_data:
            result["InfoMsg"] = "suppDebugLevel missing from JSON data"
            resp.media = result
            return
        if "driverDebugLevel" not in post_data:
            result["InfoMsg"] = "driverDebugLevel missing from JSON data"
            resp.media = result
            return

        supp_level = post_data.get("suppDebugLevel").lower()
        if supp_level not in VALID_SUPPLICANT_DEBUG_LEVELS:
            result[
                "InfoMsg"
            ] = f"suppDebugLevel must be one of {VALID_SUPPLICANT_DEBUG_LEVELS}"
            resp.media = result
            return

        try:
            await LogsService.set_supplicant_debug_level(supp_level)
        except Exception as exception:
            syslog(LOG_ERR, f"unable to set supplicant debug level: {str(exception)}")
            result["InfoMsg"] = "unable to set supplicant debug level"
            resp.media = result
            return

        drv_level = post_data.get("driverDebugLevel")
        try:
            drv_level = int(drv_level)
            if drv_level not in [0, 1]:
                raise ValueError()
        except Exception:
            result["InfoMsg"] = "driverDebugLevel must be 0 or 1"
            resp.media = result
            return

        try:
            LogsService.set_wifi_driver_debug_level(drv_level)
        except Exception as exception:
            syslog(LOG_ERR, f"unable to set driver debug level: {str(exception)}")
            result["InfoMsg"] = "unable to set driver debug level"
            resp.media = result
            return

        result["SDCERR"] = 0
        result[
            "InfoMsg"
        ] = f"Supplicant debug level = {supp_level}; Driver debug level = {drv_level}"

        resp.media = result

    async def on_get(self, _, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 0, "InfoMsg": ""}

        try:
            result["suppDebugLevel"] = await LogsService.get_supplicant_debug_level()
        except Exception as exception:
            syslog(
                LOG_ERR, f"Unable to determine supplicant debug level: {str(exception)}"
            )
            result["Errormsg"] = "Unable to determine supplicant debug level"
            result["SDCERR"] = 1

        try:
            result["driverDebugLevel"] = str(LogsService.get_wifi_driver_debug_level())
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to determine driver debug level: {str(exception)}")
            if result.get("SDCERR") == 0:
                result["Errormsg"] = "Unable to determine driver debug level"
            else:
                result[
                    "Errormsg"
                ] = "Unable to determine supplicant nor driver debug level"
            result["SDCERR"] = 1

        resp.media = result
