"""
Legacy 'definitions' module
"""

from syslog import syslog
import falcon.asgi
from summit_rcm import definition
from summit_rcm.settings import ServerConfig, SystemSettingsManage


class DefinitionsResource(object):
    """Resource to handle definitions requests"""

    async def on_get(self, req, resp):
        """GET handler for /definitions endpoint"""
        try:
            plugins = []
            for k in ServerConfig().get_parser().options("plugins"):
                plugins.append(k)
            plugins.sort()

            settings = {}
            # If sessions aren't enabled, set the session_timeout to -1 to alert the frontend that we
            # don't need to auto log out.
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
