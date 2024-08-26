#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Legacy 'definitions' module
"""

from syslog import syslog
import falcon.asgi
from summit_rcm.settings import ServerConfig, SystemSettingsManage
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm import definition

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        DefinitionsResponseModelLegacy,
    )
    from summit_rcm.rest_api.utils.spectree.tags import system_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    DefinitionsResponseModelLegacy = None
    system_tag = None


spec = SpectreeService()


class DefinitionsResource(object):
    """Resource to handle definitions requests"""

    @spec.validate(
        resp=Response(
            HTTP_200=DefinitionsResponseModelLegacy,
        ),
        tags=[system_tag],
        deprecated=True,
    )
    async def on_get(self, req, resp):
        """Retrieve definitions (legacy)"""
        try:
            plugins = []
            for k in ServerConfig().get_parser().options("plugins"):
                plugins.append(k)
            plugins.sort()

            settings = {}
            # If sessions aren't enabled, set the session_timeout to -1 to alert the frontend that
            # we don't need to auto log out.
            settings["session_timeout"] = (
                SystemSettingsManage.get_session_timeout()
                if ServerConfig()
                .get_parser()
                .getboolean("/", "tools.sessions.on", fallback=True)
                else -1
            )

            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
            resp.media = {
                "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"],
                "InfoMsg": "",
                "Definitions": {
                    "SDCERR": definition.SUMMIT_RCM_ERRORS,
                    "PERMISSIONS": definition.USER_PERMISSION_TYPES,
                    "DEVICE_TYPES": definition.SUMMIT_RCM_DEVTYPE_TEXT,
                    "DEVICE_STATES": definition.SUMMIT_RCM_STATE_TEXT,
                    "PLUGINS": plugins,
                    "SETTINGS": settings,
                },
            }
        except Exception as exception:
            syslog(f"Could not get definitions: {str(exception)}")
            resp.status = falcon.HTTP_500
