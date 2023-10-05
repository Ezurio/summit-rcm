"""Init File to setup the Stunnel Plugin"""
from syslog import syslog, LOG_ERR
import summit_rcm


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
