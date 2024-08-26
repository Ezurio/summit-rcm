#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to handle version requests (legacy)
"""

import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.services.version_service import VersionService
from summit_rcm import definition

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        UnauthorizedErrorResponseModel,
        VersionInfoLegacy,
    )
    from summit_rcm.rest_api.utils.spectree.tags import system_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    UnauthorizedErrorResponseModel = None
    VersionInfoLegacy = None
    system_tag = None


spec = SpectreeService()


class Version:
    @spec.validate(
        resp=Response(
            HTTP_200=VersionInfoLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
        deprecated=True,
    )
    async def on_get(self, req, resp):
        """
        Retrieve version info (legacy)
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        try:
            version = await VersionService().get_version(is_legacy=True)
            version["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            version["InfoMsg"] = ""
        except Exception as e:
            version = {
                "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
                "InfoMsg": f"An exception occurred while trying to get versioning info: {e}",
            }
        resp.media = version
