#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Init file to setup the plugin to allow unauthenticated access to the reset and reboot endpoints
"""

from syslog import syslog, LOG_ERR
from typing import Optional
import summit_rcm


async def get_legacy_supported_routes():
    """Optional Function to return supported legacy routes"""
    routes = []
    routes.append("/allowUnauthenticatedResetReboot")
    return routes


async def get_legacy_routes():
    """
    Function to import and return the API Routes to allow unauthenticated access to the reset and
    reboot endpoints
    """
    routes = {}
    try:
        from summit_rcm_unauthenticated.rest_api.legacy.unauthenticated import (
            AllowUnauthenticatedResourceLegacy,
        )

        summit_rcm.SessionCheckingMiddleware().paths.append(
            "/allowUnauthenticatedResetReboot"
        )
        routes["/allowUnauthenticatedResetReboot"] = (
            AllowUnauthenticatedResourceLegacy()
        )
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
    """
    Function to import and return the API Routes to allow unauthenticated access to the reset and
    reboot endpoints
    """
    routes = {}
    try:
        from summit_rcm_unauthenticated.rest_api.v2.system.unauthenticated import (
            AllowUnauthenticatedResource,
        )

        summit_rcm.SessionCheckingMiddleware().paths.append(
            "/api/v2/system/allowUnauthenticatedResetReboot"
        )
        routes["/api/v2/system/allowUnauthenticatedResetReboot"] = (
            AllowUnauthenticatedResource()
        )
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
    try:
        from summit_rcm_unauthenticated.services.unauthenticated_service import (
            UnauthenticatedService,
        )
    except ImportError:
        return

    restricted_paths = summit_rcm.SessionCheckingMiddleware().paths
    if UnauthenticatedService().get_allow_unauthenticated_enabled():
        if "/api/v2/system/power" in restricted_paths:
            restricted_paths.remove("/api/v2/system/power")
        if "/api/v2/system/factoryReset" in restricted_paths:
            restricted_paths.remove("/api/v2/system/factoryReset")
        if "reboot" in restricted_paths:
            restricted_paths.remove("reboot")
        if "factoryReset" in restricted_paths:
            restricted_paths.remove("factoryReset")
