#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""Init File to setup the Firewall Plugin"""

from syslog import syslog, LOG_ERR
from typing import Optional
import summit_rcm


async def get_legacy_supported_routes():
    """Optional Function to return supported legacy routes"""
    routes = []
    routes.append("/firewall")
    routes.append("/firewall/")
    return routes


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


async def get_v2_supported_routes():
    """Optional Function to return supported v2 routes"""
    routes = []
    routes.append("/api/v2/network/firewall")
    routes.append("/api/v2/network/firewall/forwardedPorts")
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
        routes["/api/v2/network/firewall/forwardedPorts"] = (
            FirewallForwardedPortsResource()
        )
    except ImportError:
        pass
    except Exception as exception:
        syslog(LOG_ERR, f"Error Importing firewall v2 routes: {str(exception)}")
    return routes


async def get_middleware() -> Optional[list]:
    """Handler called when adding Falcon middleware"""
    return None


async def server_config_preload_hook(_) -> None:
    """Hook function called before the Uvicorn ASGI server config is loaded"""


async def server_config_postload_hook(_) -> None:
    """Hook function called after the Uvicorn ASGI server config is loaded"""
