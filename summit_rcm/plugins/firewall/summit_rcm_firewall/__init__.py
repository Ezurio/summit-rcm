"""Init File to setup the Firewall Plugin"""
from syslog import syslog, LOG_ERR
import summit_rcm


async def get_legacy_routes():
    """Function to import and return Firewall API Routes"""
    routes = {}
    try:
        from summit_rcm_firewall.services.firewall_service import (
            FirewallService,
        )
        from summit_rcm_firewall.rest_api.legacy.firewall import (
            FirewallResourceLegacy,
        )

        routes["/firewall"] = FirewallResourceLegacy()
        routes["/firewall/{command}"] = FirewallResourceLegacy()
    except ImportError:
        pass
    except Exception as exception:
        syslog(LOG_ERR, f"Error Importing firewall legacy routes: {str(exception)}")
    return routes


async def get_v2_routes():
    """Function to import and return Firewall API Routes"""
    routes = {}
    try:
        from summit_rcm_firewall.services.firewall_service import (
            FirewallService,
        )
        from summit_rcm_firewall.rest_api.v2.network.firewall import (
            FirewallForwardedPortsResource,
        )

        summit_rcm.SessionCheckingMiddleware().paths.append("/api/v2/network/firewall")
        routes["/api/v2/network/firewall/forwardedPorts"] = FirewallForwardedPortsResource()
    except ImportError:
        pass
    except Exception as exception:
        syslog(LOG_ERR, f"Error Importing firewall v2 routes: {str(exception)}")
    return routes
