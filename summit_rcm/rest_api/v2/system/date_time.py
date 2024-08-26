#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to interact with system date/time settings
"""

from syslog import LOG_ERR, syslog
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.services.date_time_service import DateTimeService

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        GetDateTimeResponseModel,
        InternalServerErrorResponseModel,
        SetDateTimeRequestModel,
        UnauthorizedErrorResponseModel,
    )
    from summit_rcm.rest_api.utils.spectree.tags import system_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    GetDateTimeResponseModel = None
    InternalServerErrorResponseModel = None
    SetDateTimeRequestModel = None
    UnauthorizedErrorResponseModel = None
    system_tag = None


spec = SpectreeService()


class DateTimeResource(object):
    """
    Resource to handle queries and requests for the system date/time settings
    """

    def get_date_time_info(self) -> dict:
        """
        Retrieve a dictionary of current system date/time settings
        - zones
        - zone
        - datetime
        """
        result = {"zones": [], "zone": "", "datetime": ""}

        result["zones"] = DateTimeService().zones
        result["zone"] = DateTimeService().local_zone

        success, msg = DateTimeService.check_current_date_and_time()
        result["datetime"] = msg.strip() if success else ""
        return result

    @spec.validate(
        resp=Response(
            HTTP_200=GetDateTimeResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        Retrieve current date/time info
        """
        try:
            resp.media = self.get_date_time_info()
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to retrieve system date/time settings: {str(exception)}",
            )
            resp.status = falcon.HTTP_500

    @spec.validate(
        json=SetDateTimeRequestModel,
        resp=Response(
            HTTP_200=GetDateTimeResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        Set the current date/time and/or time zone
        """
        try:
            post_data: dict = await req.get_media()

            # We only check for the 'zone' and 'datetime' parameters - setting of 'zones' isn't
            # currently supported.
            zone = post_data.get("zone", "")
            date_time = post_data.get("datetime", "")

            if zone != "":
                try:
                    await DateTimeService.set_time_zone(zone)
                except Exception as exception:
                    syslog(LOG_ERR, f"Could not set timezone: {str(exception)}")
                    resp.status = falcon.HTTP_500
                    return

            if date_time != "":
                try:
                    await DateTimeService.set_time_manual(date_time)
                except Exception as exception:
                    syslog(LOG_ERR, f"Could not set datetime: {str(exception)}")
                    resp.status = falcon.HTTP_500
                    return

            resp.media = self.get_date_time_info()
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to configure system date/time settings: {str(exception)}",
            )
            resp.status = falcon.HTTP_500
