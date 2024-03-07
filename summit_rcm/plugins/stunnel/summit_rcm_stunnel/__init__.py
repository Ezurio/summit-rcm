"""Init File to setup the Stunnel Plugin"""

from syslog import syslog, LOG_ERR
from typing import Optional
import summit_rcm


async def get_legacy_supported_routes():
    """Optional Function to return supported legacy routes"""
    routes = []
    routes.append("/stunnel")
    return routes


async def get_legacy_routes():
    """Function to import and return Stunnel API Routes"""
    routes = {}
    try:
        from summit_rcm_stunnel.services.stunnel_service import StunnelService
        from summit_rcm_stunnel.rest_api.legacy.stunnel import StunnelResourceLegacy

        routes["/stunnel"] = StunnelResourceLegacy()
    except ImportError:
        pass
    except Exception as exception:
        syslog(LOG_ERR, f"Error Importing stunnel legacy routes: {str(exception)}")
    return routes


async def get_v2_supported_routes():
    """Optional Function to return supported v2 routes"""
    routes = []
    routes.append("/api/v2/network/stunnel")
    return routes


async def get_v2_routes():
    """Function to import and return Stunnel API Routes"""
    routes = {}
    try:
        from summit_rcm_stunnel.services.stunnel_service import StunnelService
        from summit_rcm_stunnel.rest_api.v2.network.stunnel import StunnelResource

        summit_rcm.SessionCheckingMiddleware().paths.append("/api/v2/network/stunnel")
        routes["/api/v2/network/stunnel"] = StunnelResource()
    except ImportError:
        pass
    except Exception as exception:
        syslog(LOG_ERR, f"Error Importing stunnel v2 routes: {str(exception)}")
    return routes


async def get_middleware() -> Optional[list]:
    """Handler called when adding Falcon middleware"""
    return None


async def server_config_preload_hook(_) -> None:
    """Hook function called before the Uvicorn ASGI server config is loaded"""


async def server_config_postload_hook(_) -> None:
    """Hook function called after the Uvicorn ASGI server config is loaded"""
