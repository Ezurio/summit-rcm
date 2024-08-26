#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""Module to handle legacy date/time endpoint"""

from syslog import syslog, LOG_ERR
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.definition import SUMMIT_RCM_ERRORS
from summit_rcm.services.date_time_service import DateTimeService

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        UnauthorizedErrorResponseModel,
        GetDateTimeResponseModelLegacy,
        SetDateTimeRequestModelLegacy,
        SetDateTimeResponseModelLegacy,
    )
    from summit_rcm.rest_api.utils.spectree.tags import system_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    UnauthorizedErrorResponseModel = None
    GetDateTimeResponseModelLegacy = None
    SetDateTimeRequestModelLegacy = None
    SetDateTimeResponseModelLegacy = None
    system_tag = None


spec = SpectreeService()


class DateTimeSetting:
    """
    Date/time management
    """

    @spec.validate(
        resp=Response(
            HTTP_200=GetDateTimeResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
        deprecated=True,
    )
    async def on_get(self, req, resp):
        """
        Retrieve current date/time info (legacy)
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "",
        }

        result["zones"] = DateTimeService().zones
        result["zone"] = DateTimeService().local_zone

        success, msg = DateTimeService.check_current_date_and_time()
        if success:
            result["method"] = "auto"
            result["time"] = msg.strip()
        else:
            result["method"] = "manual"
            result["time"] = ""

        resp.media = result

    @spec.validate(
        json=SetDateTimeRequestModelLegacy,
        resp=Response(
            HTTP_200=SetDateTimeResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
        deprecated=True,
    )
    async def on_put(self, req, resp):
        """
        Set the current date/time and/or time zone (legacy)
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "",
        }

        post_data = await req.get_media()
        zone = post_data.get("zone", "")
        method = post_data.get("method", "")
        dt = post_data.get("datetime", "")

        # Setting the timezone was initially supported when 'zone' was not an empty string so
        # re-create that here.
        if zone != "":
            try:
                await DateTimeService.set_time_zone(zone)
            except Exception as exception:
                syslog(LOG_ERR, f"Could not set timezone: {str(exception)}")
                result["InfoMsg"] = f"Could not set timezone: {str(exception)}"
                result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
                resp.media = result
                return
        # Setting the time was initially supported when 'method' is set to 'manual' so re-create
        # that here.
        elif method == "manual" and dt != "":
            try:
                await DateTimeService.set_time_manual(dt)
            except Exception as exception:
                syslog(LOG_ERR, f"Could not set datetime: {str(exception)}")
                result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
                result["InfoMsg"] = "Could not set datetime"
                resp.media = result
                return

        # Unless we hit an error, the previous logic would return the current date and time (and
        # timezone), so re-create that here.
        success, msg = DateTimeService.check_current_date_and_time()
        if success:
            result["time"] = msg
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            result["InfoMsg"] = DateTimeService().local_zone
        else:
            result["InfoMsg"] = msg
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
        resp.media = result
