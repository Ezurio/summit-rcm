#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to support configuration of the radio's SISO mode parameter for legacy routes.
"""

import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm import definition
from summit_rcm_radio_siso_mode.services.radio_siso_mode_service import (
    RadioSISOModeEnum,
    RadioSISOModeService,
)

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        InternalServerErrorResponseModel,
        UnauthorizedErrorResponseModel,
    )
    from summit_rcm_radio_siso_mode.rest_api.utils.spectree.models import (
        SISOModeStateResponseModelLegacy,
        SISOModeStateModelLegacy,
    )
    from summit_rcm.rest_api.utils.spectree.tags import network_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    InternalServerErrorResponseModel = None
    UnauthorizedErrorResponseModel = None
    SISOModeStateResponseModelLegacy = None
    SISOModeStateModelLegacy = None
    network_tag = None


spec = SpectreeService()


class RadioSISOModeResourceLegacy:
    """
    Resource to expose SISO mode configuration
    """

    @spec.validate(
        resp=Response(
            HTTP_200=SISOModeStateResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
        deprecated=True,
    )
    async def on_get(self, req, resp):
        """
        Retrieve the current radio SISO mode configuration (legacy)
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

    @spec.validate(
        json=SISOModeStateModelLegacy,
        resp=Response(
            HTTP_200=SISOModeStateResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
        deprecated=True,
    )
    async def on_put(self, req, resp):
        """
        Update the radio's SISO mode configuration (legacy)
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
            RadioSISOModeService.set_siso_mode(RadioSISOModeEnum(siso_mode))
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
