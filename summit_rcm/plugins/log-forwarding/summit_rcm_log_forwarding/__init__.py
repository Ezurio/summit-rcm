#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""Init File to setup the Log Forwarding Plugin"""

from syslog import syslog, LOG_ERR
from typing import Optional
import summit_rcm


def get_at_commands():
    """Function to import and return Log Forwarding AT Commands"""
    at_commands = []
    try:
        from summit_rcm_log_forwarding.at_interface.commands.log_forwarding_command import (
            LogForwardingCommand,
        )

        at_commands.extend([LogForwardingCommand])
    except ImportError:
        pass
    except Exception as exception:
        syslog(LOG_ERR, f"Error Importing log forwarding AT Commands: {str(exception)}")
    return at_commands


async def get_legacy_supported_routes():
    """Optional Function to return supported legacy routes"""
    routes = []
    routes.append("/logForwarding")
    return routes


async def get_legacy_routes():
    """Function to import and return Log Forwarding API Routes"""
    routes = {}
    try:
        from summit_rcm_log_forwarding.services.log_forwarding_service import (
            LogForwardingService,
        )
        from summit_rcm_log_forwarding.rest_api.legacy.log_forwarding import (
            LogForwarding,
        )

        summit_rcm.SessionCheckingMiddleware().paths.append("logForwarding")
        routes["/logForwarding"] = LogForwarding()
    except ImportError:
        pass
    except Exception as exception:
        syslog(
            LOG_ERR, f"Error Importing log forwarding legacy routes: {str(exception)}"
        )
    return routes


async def get_v2_supported_routes():
    """Optional Function to return supported v2 routes"""
    routes = []
    routes.append("/api/v2/system/logs/forwarding")
    return routes


async def get_v2_routes():
    """Function to import and return Log Forwarding API Routes"""
    routes = {}
    try:
        from summit_rcm_log_forwarding.services.log_forwarding_service import (
            LogForwardingService,
        )
        from summit_rcm_log_forwarding.rest_api.v2.system.log_forwarding import (
            LogForwardingResource,
        )

        routes["/api/v2/system/logs/forwarding"] = LogForwardingResource()
    except ImportError:
        pass
    except Exception as exception:
        syslog(LOG_ERR, f"Error Importing log forwarding v2 routes: {str(exception)}")
    return routes


async def get_middleware() -> Optional[list]:
    """Handler called when adding Falcon middleware"""
    return None


async def server_config_preload_hook(_) -> None:
    """Hook function called before the Uvicorn ASGI server config is loaded"""


async def server_config_postload_hook(_) -> None:
    """Hook function called after the Uvicorn ASGI server config is loaded"""
