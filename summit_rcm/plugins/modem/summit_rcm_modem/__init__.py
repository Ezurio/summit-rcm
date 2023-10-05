"""Init File to setup the Modem Plugin"""
from syslog import syslog, LOG_ERR
import summit_rcm


async def get_legacy_routes():
    """Function to import and return Modem API Routes"""
    routes = {}
    try:
        from summit_rcm_modem.rest_api.legacy.modem import (
            PositioningSwitch,
            Positioning,
            ModemFirmwareUpdate,
            ModemEnable,
        )

        summit_rcm.SessionCheckingMiddleware().paths.append("modemEnable")
        routes["/positioning"] = Positioning()
        routes["/positioningSwitch"] = PositioningSwitch()
        routes["/modemFirmwareUpdate"] = ModemFirmwareUpdate()
        routes["/modemEnable"] = ModemEnable()
    except ImportError:
        pass
    except Exception as exception:
        syslog(LOG_ERR, f"Error Importing modem legacy routes: {str(exception)}")
    return routes
