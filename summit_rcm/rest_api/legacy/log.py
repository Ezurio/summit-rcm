"""
Module to handle log configuration for legacy routes
"""

from syslog import LOG_ERR, syslog
import falcon
from summit_rcm.services.logs_service import (
    VALID_SUPPLICANT_DEBUG_LEVELS,
    JournalctlError,
    LogsService,
)


class LogData:
    """Resource to handle queries and requests for log data"""

    async def on_get(self, req, resp):
        """
        GET handler for the /logData endpoint
        """
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


class LogSetting:
    """Resource to handle queries and requests for log level configuration"""

    async def on_post(self, req, resp):
        """
        POST handler for the /logSetting endpoint
        """
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
        """
        GET handler for the /logSetting endpoint
        """
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
