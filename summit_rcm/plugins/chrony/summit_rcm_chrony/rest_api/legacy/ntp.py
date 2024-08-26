#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to support NTP configuration via chrony for legacy routes.
"""

import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm_chrony.services.ntp_service import ChronyNTPService, SOURCE_COMMANDS
from summit_rcm.definition import SUMMIT_RCM_ERRORS

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        UnauthorizedErrorResponseModel,
        DefaultResponseModelLegacy,
    )
    from summit_rcm_chrony.rest_api.utils.spectree.models import (
        ChronySourcesResponseModelLegacy,
        ChronySourcesRequestModelLegacy,
    )
    from summit_rcm.rest_api.utils.spectree.tags import system_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    UnauthorizedErrorResponseModel = None
    DefaultResponseModelLegacy = None
    ChronySourcesResponseModelLegacy = None
    ChronySourcesRequestModelLegacy = None
    system_tag = None


spec = SpectreeService()


class NTPResourceLegacy:
    """
    Resource to expose chrony NTP configuration
    """

    @staticmethod
    def result_parameter_not_one_of(parameter: str, supplied_value: str, not_one_of):
        """
        Generate return object value for when a supplied value is not valid
        """
        return {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": f"supplied parameter '{parameter}' value {supplied_value} must be one of"
            f" {not_one_of}, ",
        }

    @spec.validate(
        resp=Response(
            HTTP_200=ChronySourcesResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
        deprecated=True,
    )
    async def on_get(self, _, resp: falcon.asgi.Response) -> None:
        """
        Retrieve chrony NTP sources (legacy)
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "",
        }

        try:
            result["sources"] = await ChronyNTPService.chrony_get_sources()
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as exception:
            result["sources"] = []
            result["InfoMsg"] = f"Unable to retrieve chrony sources - {str(exception)}"
        resp.media = result

    @spec.validate(
        json=ChronySourcesRequestModelLegacy,
        resp=Response(
            HTTP_200=DefaultResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        path_parameter_descriptions={"command": "The command to execute"},
        security=SpectreeService().security,
        tags=[system_tag],
        deprecated=True,
    )
    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response, command: str
    ) -> None:
        """
        Update chrony NTP sources (legacy)
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "",
        }

        try:
            post_data = await req.get_media()

            if command:
                if command not in SOURCE_COMMANDS:
                    result.update(
                        self.result_parameter_not_one_of(
                            "command", command, SOURCE_COMMANDS
                        )
                    )
                else:
                    await ChronyNTPService.chrony_configure_sources(
                        command, post_data.get("sources", [])
                    )
                    result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            else:
                result["InfoMsg"] = "No command specified"
        except Exception as exception:
            result["InfoMsg"] = f"Unable to update chrony sources - {str(exception)}"

        resp.media = result
