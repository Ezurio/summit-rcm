#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""Init File to setup the Bluetooth Plugin"""

from syslog import syslog, LOG_ERR
from typing import Optional
import summit_rcm


async def get_legacy_supported_routes():
    """Optional Function to return supported legacy routes"""
    routes = []
    routes.append("/allowUnauthenticatedResetReboot")
    return routes


async def get_legacy_routes():
    """Function to import and return bluetooth API Routes"""
    routes = {}
    try:
        from summit_rcm_unauthenticated.rest_api.legacy.unauthenticated import (
            AllowUnauthenticatedResourceLegacy,
        )
        from summit_rcm_unauthenticated.services.unauthenticated_service import (
            UnauthenticatedService,
        )

        routes["/allowUnauthenticatedResetReboot"] = (
            AllowUnauthenticatedResourceLegacy()
        )
        unauthenticated = UnauthenticatedService().get_allow_unauthenticated_enabled()
        if "reboot" in summit_rcm.summit_rcm_plugins and unauthenticated:
            summit_rcm.summit_rcm_plugins.remove("reboot")
        if "factoryReset" in summit_rcm.summit_rcm_plugins and unauthenticated:
            summit_rcm.summit_rcm_plugins.remove("factoryReset")
    except ImportError:
        pass
    except Exception as exception:
        syslog(
            LOG_ERR, f"Error Importing unauthenticated legacy routes: {str(exception)}"
        )
    return routes


async def get_v2_supported_routes():
    """Optional Function to return supported v2 routes"""
    routes = []
    routes.append("/api/v2/system/allowUnauthenticatedResetReboot")
    return routes


async def get_v2_routes():
    """Function to import and return bluetooth API Routes"""
    routes = {}
    try:
        from summit_rcm_unauthenticated.rest_api.v2.system.unauthenticated import (
            AllowUnauthenticatedResource,
        )
        from summit_rcm_unauthenticated.services.unauthenticated_service import (
            UnauthenticatedService,
        )

        routes["/api/v2/system/allowUnauthenticatedResetReboot"] = (
            AllowUnauthenticatedResource()
        )
        unauthenticated = UnauthenticatedService().get_allow_unauthenticated_enabled()
        restricted_paths = summit_rcm.SessionCheckingMiddleware().paths
        if "/api/v2/system/power" in restricted_paths and unauthenticated:
            restricted_paths.remove("/api/v2/system/power")
        if "/api/v2/system/factoryReset" in restricted_paths and unauthenticated:
            restricted_paths.remove("/api/v2/system/factoryReset")
    except ImportError:
        pass
    except Exception as exception:
        syslog(LOG_ERR, f"Error Importing unauthenticated v2 routes: {str(exception)}")
    return routes


async def get_middleware() -> Optional[list]:
    """Handler called when adding Falcon middleware"""
    return None


async def server_config_preload_hook(_) -> None:
    """Hook function called before the Uvicorn ASGI server config is loaded"""


async def server_config_postload_hook(_) -> None:
    """Hook function called after the Uvicorn ASGI server config is loaded"""
