"""Init File to setup the AWM Plugin"""
from syslog import syslog, LOG_ERR


def get_at_commands():
    """Function to import and return AWM AT Commands"""
    at_commands = []
    try:
        from summit_rcm_awm.at_interface.commands.awm_mode_command import (
            AWMModeCommand,
        )
        from summit_rcm_awm.at_interface.commands.awm_scan_command import (
            AWMScanCommand,
        )

        at_commands.extend([AWMModeCommand, AWMScanCommand])
    except ImportError:
        pass
    except Exception as exception:
        syslog(LOG_ERR, f"Error Importing AWM AT Commands: {str(exception)}")
    return at_commands


async def get_legacy_routes():
    """Function to import and return AWM API Routes"""
    routes = {}
    try:
        from summit_rcm_awm.services.awm_config_service import AWMConfigService
        from summit_rcm_awm.rest_api.legacy.awm import AWMResourceLegacy

        routes["/awm"] = AWMResourceLegacy()
    except ImportError:
        pass
    except Exception as exception:
        syslog(LOG_ERR, f"Error Importing AWM legacy routes: {str(exception)}")
    return routes


async def get_v2_routes():
    """Function to import and return AWM API Routes"""
    routes = {}
    try:
        from summit_rcm_awm.services.awm_config_service import AWMConfigService
        from summit_rcm_awm.rest_api.v2.network.awm import AWMResource

        routes["/api/v2/network/wifi/awm"] = AWMResource()
    except ImportError:
        pass
    except Exception as exception:
        syslog(LOG_ERR, f"Error Importing AWM v2 routes: {str(exception)}")
    return routes
