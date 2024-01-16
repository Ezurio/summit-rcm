"""Init File to setup the Radio SISO Mode Plugin"""
from syslog import syslog, LOG_ERR
from typing import Optional


def get_at_commands():
    """Function to import and return Radio SISO Mode AT Commands"""
    at_commands = []
    try:
        from summit_rcm_radio_siso_mode.at_interface.commands.siso_mode_command import (
            SISOModeCommand,
        )

        at_commands.extend([SISOModeCommand])
    except ImportError:
        pass
    except Exception as exception:
        syslog(
            LOG_ERR, f"Error Importing radio SISO mode AT Commands: {str(exception)}"
        )
    return at_commands


async def get_legacy_routes():
    """Function to import and return Radio SISO Mode API Routes"""
    routes = {}
    try:
        from summit_rcm_radio_siso_mode.services.radio_siso_mode_service import (
            RadioSISOModeService,
        )
        from summit_rcm_radio_siso_mode.rest_api.legacy.radio_siso_mode import (
            RadioSISOModeResourceLegacy,
        )

        routes["/radioSISOMode"] = RadioSISOModeResourceLegacy()
    except ImportError:
        pass
    except Exception as exception:
        syslog(
            LOG_ERR, f"Error Importing radio SISO mode legacy routes: {str(exception)}"
        )
    return routes


async def get_v2_routes():
    """Function to import and return Radio SISO Mode API Routes"""
    routes = {}
    try:
        from summit_rcm_radio_siso_mode.services.radio_siso_mode_service import (
            RadioSISOModeService,
        )
        from summit_rcm_radio_siso_mode.rest_api.v2.network.radio_siso_mode import (
            RadioSISOModeResource,
        )

        routes["/api/v2/network/wifi/radioSISOMode"] = RadioSISOModeResource()
    except ImportError:
        pass
    except Exception as exception:
        syslog(LOG_ERR, f"Error Importing radio SISO mode v2 routes: {str(exception)}")
    return routes


async def get_middleware() -> Optional[list]:
    """Handler called when adding Falcon middleware"""
    return None


async def server_config_preload_hook(_) -> None:
    """Hook function called before the Uvicorn ASGI server config is loaded"""


async def server_config_postload_hook(_) -> None:
    """Hook function called after the Uvicorn ASGI server config is loaded"""
