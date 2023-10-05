"""Init File to setup the Chrony Plugin"""
from syslog import syslog, LOG_ERR


def get_at_commands():
    """Function to import and return Chrony AT Commands"""
    at_commands = []
    try:
        from summit_rcm_chrony.at_interface.commands.ntp_configure_command import (
            NTPConfigureCommand,
        )
        from summit_rcm_chrony.at_interface.commands.ntp_get_command import (
            NTPGetCommand,
        )

        at_commands.extend([NTPConfigureCommand, NTPGetCommand])
    except ImportError:
        pass
    except Exception as exception:
        syslog(LOG_ERR, f"Error Importing chrony AT Commands: {str(exception)}")
    return at_commands


async def get_legacy_routes():
    """Function to import and return Chrony API Routes"""
    routes = {}
    try:
        from summit_rcm_chrony.services.ntp_service import ChronyNTPService
        from summit_rcm_chrony.rest_api.legacy.ntp import NTPResourceLegacy

        routes["/ntp"] = NTPResourceLegacy()
        routes["/ntp/{command}"] = NTPResourceLegacy()
    except ImportError:
        pass
    except Exception as exception:
        syslog(LOG_ERR, f"Error Importing chrony legacy routes: {str(exception)}")
    return routes


async def get_v2_routes():
    """Function to import and return Chrony API Routes"""
    routes = {}
    try:
        from summit_rcm_chrony.services.ntp_service import ChronyNTPService
        from summit_rcm_chrony.rest_api.v2.system.ntp import (
            NTPSourcesResource,
            NTPSourceResource,
        )

        routes["/api/v2/system/datetime/ntp"] = NTPSourcesResource()
        routes["/api/v2/system/datetime/ntp/{address}"] = NTPSourceResource()
    except ImportError:
        pass
    except Exception as exception:
        syslog(LOG_ERR, f"Error Importing chrony v2 routes: {str(exception)}")
    return routes
