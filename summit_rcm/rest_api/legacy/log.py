"""
Module to handle log configuration for legacy routes
"""

from syslog import LOG_ERR, syslog
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.definition import (
    DriverLogLevelEnum,
    JournalctlLogTypesEnum,
    SupplicantLogLevelEnum,
)
from summit_rcm.services.logs_service import (
    JournalctlError,
    LogsService,
)

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        DefaultResponseModelLegacy,
        UnauthorizedErrorResponseModel,
        LogsDataRequestQuery,
        LogsDataResponseModelLegacy,
        LogVerbosity,
        LogVerbosityResponseModelLegacy,
    )
    from summit_rcm.rest_api.utils.spectree.tags import system_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    DefaultResponseModelLegacy = None
    UnauthorizedErrorResponseModel = None
    LogsDataRequestQuery = None
    LogsDataResponseModelLegacy = None
    LogVerbosity = None
    LogVerbosityResponseModelLegacy = None
    system_tag = None


spec = SpectreeService()


class LogData:
    """Resource to handle queries and requests for log data"""

    @spec.validate(
        query=LogsDataRequestQuery,
        resp=Response(
            HTTP_200=LogsDataResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
        deprecated=True,
    )
    async def on_get(self, req, resp):
        """
        Retrieve journal log data (legacy)
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
        try:
            typ = JournalctlLogTypesEnum(req.params.get("type", "All"))
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Error parsing 'type' parameter: {str(exception)}",
            )
            resp.media = {"SDCERR": 1, "InfoMsg": "Invalid log type"}
            return
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

    @spec.validate(
        json=LogVerbosity,
        resp=Response(
            HTTP_200=DefaultResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
        deprecated=True,
    )
    async def on_post(self, req, resp):
        """
        Set the log verbosity levels for the supplicant and Wi-Fi driver (legacy)
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

        try:
            supp_level = SupplicantLogLevelEnum(post_data.get("suppDebugLevel").lower())
        except ValueError:
            result["InfoMsg"] = (
                f"suppDebugLevel must be one of {[e.value for e in SupplicantLogLevelEnum]}"
            )
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
            drv_level = DriverLogLevelEnum(drv_level)
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
        result["InfoMsg"] = (
            f"Supplicant debug level = {supp_level}; Driver debug level = {drv_level}"
        )

        resp.media = result

    @spec.validate(
        resp=Response(
            HTTP_200=LogVerbosityResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
        deprecated=True,
    )
    async def on_get(self, _, resp):
        """
        Retrieve current log verbosity levels for the supplicant and Wi-Fi driver (legacy)
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 0, "InfoMsg": ""}

        try:
            result["suppDebugLevel"] = (
                await LogsService.get_supplicant_debug_level()
            ).value
        except Exception as exception:
            syslog(
                LOG_ERR, f"Unable to determine supplicant debug level: {str(exception)}"
            )
            result["Errormsg"] = "Unable to determine supplicant debug level"
            result["SDCERR"] = 1

        try:
            result["driverDebugLevel"] = str(
                LogsService.get_wifi_driver_debug_level().value
            )
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to determine driver debug level: {str(exception)}")
            if result.get("SDCERR") == 0:
                result["Errormsg"] = "Unable to determine driver debug level"
            else:
                result["Errormsg"] = (
                    "Unable to determine supplicant nor driver debug level"
                )
            result["SDCERR"] = 1

        resp.media = result
