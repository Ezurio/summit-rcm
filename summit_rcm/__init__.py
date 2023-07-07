"""
Summit RCM main module
"""

import asyncio
from syslog import LOG_ERR, syslog, openlog
from typing import Any, List
import falcon.asgi
from summit_rcm.services.date_time_service import DateTimeService
from summit_rcm.settings import ServerConfig

summit_rcm_plugins: List[str] = []


app = falcon.asgi.App()


class SecureHeadersMiddleware:
    """Middleware that enables the use of secure headers"""

    async def process_response(self, req, resp, resource, req_succeeded):
        """Add secure headers to the response before it's returned to the client"""
        headers = resp.headers
        headers["X-Frame-Options"] = "DENY"
        headers["X-XSS-Protection"] = "1; mode=block"
        headers["X-Content-Type-Options"] = "nosniff"
        headers["Content-Security-Policy"] = "default-src 'self'"
        # Add Strict-Transport headers
        headers["Strict-Transport-Security"] = "max-age=600"  # ten minutes


class LifespanMiddleware:
    """Middleware that handles ASGI lifespan events"""

    async def process_startup(self, scope, event):
        """Add logic to run at the startup event"""

        # If enabled, load the AT interface
        try:
            from summit_rcm.at_interface.at_interface import ATInterface
        except ImportError:
            ATInterface = None

        if ATInterface:
            syslog("Starting AT interface")
            asyncio.create_task(ATInterface(asyncio.get_event_loop()).start())

        # Load the routes
        await add_routes()


class SessionCheckingMiddleware:
    """Middleware that handles enforcing checking for a valid session"""

    def __init__(self) -> None:
        self.paths = [
            "connections",
            "connection",
            "accesspoints",
            "networkInterfaces",
            "networkInterface",
            "file",
            "users",
            "firmware",
            "logData",
            "logSetting",
            "logForwarding",
            "poweroff",
            "suspend",
            "files",
            "certificates",
            "datetime",
            "fips",
            "modemEnable",
        ]

    def session_is_valid(self, req) -> bool:
        """Determinte if the current request's session is valid"""
        if not hasattr(req.context, "valid_session"):
            return False

        if not req.context.valid_session:
            return False

        username = req.context.get_session("USERNAME")
        return username is not None and username != ""

    async def process_request(self, req, resp):
        """
        Raise HTTP 401 Unauthorized client error if a session with invalid id tries to access
        following resources.
        """
        # With the `get` method the session id will be saved which could result in session fixation
        # vulnerability. Session ids will be destroyed periodically so we have to check 'USERNAME'
        # to make sure the session is not valid after logout.
        if not self.session_is_valid(req):
            url = req.url.split("/")[-1]
            path_root = req.path.split("/")[1]
            if (
                url
                and ".html" not in url
                and ".js" not in url
                and (path_root in self.paths or path_root in summit_rcm_plugins)
            ):
                resp.status = falcon.HTTP_401
                resp.complete = True


class IndexResource:
    """Main index resource"""

    async def on_get(self, req, resp):
        """GET handler for / endpoint"""
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_TEXT
        resp.text = "Summit RCM"


async def add_definitions_legacy():
    """Add the legacy /definition route, if enabled"""
    try:
        from summit_rcm.rest_api.legacy.definitions import DefinitionsResource
    except ImportError:
        DefinitionsResource = None

    if DefinitionsResource:
        add_route("/definitions", DefinitionsResource())


async def add_firewall_legacy():
    """
    Add the following legacy routes, if enabled:
    - /firewall
    - /firewall/{command}
    """
    try:
        from summit_rcm.iptables.firewall import Firewall

        summit_rcm_plugins.append("firewall")
    except ImportError:
        Firewall = None

    if Firewall:
        try:
            add_route("/firewall", Firewall())
            add_route("/firewall/{command}", Firewall())
        except Exception as exception:
            syslog(LOG_ERR, f"Could not load firewall endpoints - {str(exception)}")
            raise exception


async def add_users_legacy():
    """
    Add the following legacy routes, if enabled:
    - /login
    - /users
    """
    try:
        from summit_rcm.rest_api.legacy.users import UserManage, LoginManage
    except ImportError:
        UserManage = None

    if UserManage:
        try:
            add_route("/login", LoginManage())
            add_route("/users", UserManage())
        except Exception as exception:
            syslog(
                LOG_ERR, f"Could not load user management endpoints - {str(exception)}"
            )
            raise exception


async def add_network_v2():
    """
    Add the following v2 routes, if enabled:
    - /api/v2/network/status
    - /api/v2/network/interfaces
    - /api/v2/network/interfaces/{name}
    - /api/v2/network/interfaces/{name}/stats
    - /api/v2/network/connections
    - /api/v2/network/connections/uuid/{uuid}
    - /api/v2/network/connections/import
    - /api/v2/network/connections/export
    - /api/v2/network/accessPoints
    - /api/v2/network/accessPoints/scan
    - /api/v2/network/certificates
    - /api/v2/network/certificates/{name}
    - /api/v2/network/wifi
    """
    try:
        from summit_rcm.rest_api.v2.network.status import NetworkStatusResource
        from summit_rcm.rest_api.v2.network.interfaces import (
            NetworkInterfacesResource,
            NetworkInterfaceResource,
            NetworkInterfaceStatsResource,
        )
        from summit_rcm.rest_api.v2.network.connections import (
            NetworkConnectionsResource,
            NetworkConnectionResourceByUuid,
            NetworkConnectionsImportResource,
            NetworkConnectionsExportResource,
        )
        from summit_rcm.rest_api.v2.network.access_points import (
            AccessPointsResource,
            AccessPointsScanResource,
        )
        from summit_rcm.rest_api.v2.network.certificates import CertificatesResource
        from summit_rcm.rest_api.v2.network.certificates import CertificateResource
        from summit_rcm.rest_api.v2.network.wifi import WiFiResource
    except ImportError:
        NetworkStatusResource = None

    if NetworkStatusResource:
        try:
            add_route("/api/v2/network/status", NetworkStatusResource())
            add_route("/api/v2/network/interfaces", NetworkInterfacesResource())
            add_route("/api/v2/network/interfaces/{name}", NetworkInterfaceResource())
            add_route(
                "/api/v2/network/interfaces/{name}/stats",
                NetworkInterfaceStatsResource(),
            )
            add_route("/api/v2/network/connections", NetworkConnectionsResource())
            add_route(
                "/api/v2/network/connections/uuid/{uuid}",
                NetworkConnectionResourceByUuid(),
            )
            add_route(
                "/api/v2/network/connections/import", NetworkConnectionsImportResource()
            )
            add_route(
                "/api/v2/network/connections/export", NetworkConnectionsExportResource()
            )
            add_route("/api/v2/network/accessPoints", AccessPointsResource())
            add_route("/api/v2/network/accessPoints/scan", AccessPointsScanResource())
            add_route("/api/v2/network/certificates", CertificatesResource())
            add_route("/api/v2/network/certificates/{name}", CertificateResource())
            add_route("/api/v2/network/wifi", WiFiResource())
        except Exception as exception:
            syslog(LOG_ERR, f"Could not load network endpoints - {str(exception)}")
            raise exception


async def add_network_legacy():
    """
    Add the following legacy routes, if enabled:
    - /networkStatus
    - /networkInterface
    - /networkInterfaces
    - /networkInterfaceStatistics
    - /connections
    - /connection
    - /accesspoints
    - /wifiEnable
    """
    try:
        from summit_rcm.rest_api.legacy.network import (
            NetworkInterfaces,
            NetworkInterface,
            NetworkInterfaceStatistics,
            NetworkConnections,
            NetworkConnection,
            NetworkAccessPoints,
            WifiEnable,
        )
        from summit_rcm.rest_api.legacy.network_status import NetworkStatus
    except ImportError:
        NetworkInterfaces = None

    if NetworkInterfaces:
        try:
            add_route("/networkStatus", NetworkStatus())
            add_route("/networkInterface", NetworkInterface())
            add_route("/networkInterfaces", NetworkInterfaces())
            add_route("/networkInterfaceStatistics", NetworkInterfaceStatistics())
            add_route("/connections", NetworkConnections())
            add_route("/connection", NetworkConnection())
            add_route("/accesspoints", NetworkAccessPoints())
            add_route("/wifiEnable", WifiEnable())
        except Exception as exception:
            syslog(LOG_ERR, f"Could not load network endpoints - {str(exception)}")
            raise exception


async def add_advanced_legacy():
    """
    Add the following legacy routes, if enabled:
    - /poweroff
    - /suspend
    - /reboot
    - /factoryReset
    - /fips
    """
    try:
        from summit_rcm.rest_api.legacy.advanced import (
            PowerOff,
            Suspend,
            Reboot,
            FactoryReset,
            Fips,
        )
    except ImportError:
        PowerOff = None

    if PowerOff:
        try:
            add_route("/poweroff", PowerOff())
            add_route("/suspend", Suspend())
            add_route("/reboot", Reboot())
            add_route("/factoryReset", FactoryReset())
            add_route("/fips", Fips())
        except Exception as exception:
            syslog(LOG_ERR, f"Could not load advanced endpoints - {str(exception)}")
            raise exception


async def add_certificates_legacy():
    """Add the /certificates legacy route, if enabled"""
    try:
        from summit_rcm.rest_api.legacy.certificates import Certificates
    except ImportError:
        Certificates = None

    if Certificates:
        try:
            add_route("/certificates", Certificates())
        except Exception as exception:
            syslog(LOG_ERR, f"Could not load certificates endpoint - {str(exception)}")
            raise exception


async def add_files_legacy():
    """
    Add the following legacy routes, if enabled:
    - /files
    - /file
    """
    try:
        from summit_rcm.rest_api.legacy.files import FileManage, FilesManage
    except ImportError:
        FileManage = None

    if FileManage:
        try:
            add_route("/files", FilesManage())
            add_route("/file", FileManage())
        except Exception as exception:
            syslog(LOG_ERR, f"Could not load file endpoints - {str(exception)}")
            raise exception


async def add_date_time_legacy():
    """Add the /datetime legacy route, if enabled"""
    try:
        from summit_rcm.rest_api.legacy.date_time import DateTimeSetting
    except ImportError:
        DateTimeSetting = None

    if DateTimeSetting:
        try:
            add_route("/datetime", DateTimeSetting())
            await DateTimeService().populate_time_zone_list()
        except Exception as exception:
            syslog(LOG_ERR, f"Could not load datetime endpoints - {str(exception)}")
            raise exception


async def add_logs_legacy():
    """
    Add the following legacy routes, if enabled:
    - /logData
    - /logSetting
    - /logForwarding
    """
    try:
        from summit_rcm.rest_api.legacy.log import LogData, LogSetting, LogForwarding
    except ImportError:
        LogData = None

    if LogData:
        try:
            add_route("/logData", LogData())
            add_route("/logSetting", LogSetting())
            add_route("/logForwarding", LogForwarding())
        except Exception as exception:
            syslog(LOG_ERR, f"Could not load logging endpoints - {str(exception)}")
            raise exception


async def add_version_legacy():
    """Add the /version legacy route, if enabled"""
    try:
        from summit_rcm.rest_api.legacy.version import Version
    except ImportError:
        Version = None

    if Version:
        try:
            add_route("/version", Version())
        except Exception as exception:
            syslog(LOG_ERR, f"Could not load version endpoint - {str(exception)}")
            raise exception


async def add_firmware_legacy():
    """Add the /firmware legacy route, if enabled"""
    try:
        from summit_rcm.rest_api.legacy.swupdate import SWUpdate
    except ImportError:
        SWUpdate = None

    if SWUpdate:
        try:
            add_route("/firmware", SWUpdate())
        except Exception as exception:
            syslog(
                LOG_ERR, f"Could not load firmware update endpoint - {str(exception)}"
            )
            raise exception


async def add_unauthenticated_legacy():
    """Add the /allowUnauthenticatedResetReboot legacy route, if enabled, and configure the logic
    for requiring a valid, authenticated session for access to the /reboot and /factoryReset
    endpoints"""
    try:
        from summit_rcm.rest_api.legacy.unauthenticated import (
            AllowUnauthenticatedResetReboot,
        )

        summit_rcm_plugins.append("allowUnauthenticatedResetReboot")
    except ImportError:
        AllowUnauthenticatedResetReboot = None

    if AllowUnauthenticatedResetReboot:
        try:
            unauthenticated = AllowUnauthenticatedResetReboot()
            if not unauthenticated.allow_unauthenticated_reset_reboot:
                summit_rcm_plugins.append("factoryReset")
                summit_rcm_plugins.append("reboot")

            add_route("/allowUnauthenticatedResetReboot", unauthenticated)
            return
        except Exception as exception:
            syslog(
                LOG_ERR,
                "Could not load endpoint to allow unauthenticated access to reset/reboot - "
                f"{str(exception)}",
            )
            raise exception

    summit_rcm_plugins.append("factoryReset")
    summit_rcm_plugins.append("reboot")


async def add_awm_legacy():
    """Add the /awm legacy route, if enabled"""
    try:
        from summit_rcm.awm.awm_config_service import AWMConfigService
        from summit_rcm.rest_api.legacy.awm import AWMResourceLegacy

        summit_rcm_plugins.append("awm")
    except ImportError:
        AWMConfigService = None
        AWMResourceLegacy = None

    if AWMConfigService and AWMResourceLegacy:
        try:
            add_route("/awm", AWMResourceLegacy())
        except Exception as exception:
            syslog(LOG_ERR, f"Could not load AWM endpoint - {str(exception)}")
            raise exception


async def add_stunnel_legacy():
    """Add the /stunnel legacy route, if enabled"""
    try:
        from summit_rcm.stunnel.stunnel import Stunnel

        summit_rcm_plugins.append("stunnel")
    except ImportError:
        Stunnel = None

    if Stunnel:
        try:
            add_route("/stunnel", Stunnel())
        except Exception as exception:
            syslog(LOG_ERR, f"Could not load stunnel endpoint - {str(exception)}")
            raise exception


async def add_modem_legacy():
    """
    Add the following legacy routes, if enabled:
    - /positioning
    - /positioningSwitch
    - /modemFirmwareUpdate
    - /modemEnable
    """
    try:
        from summit_rcm.modem.modem import (
            PositioningSwitch,
            Positioning,
            ModemFirmwareUpdate,
            ModemEnable,
        )

        summit_rcm_plugins.append("positioning")
        summit_rcm_plugins.append("positioningSwitch")
        summit_rcm_plugins.append("modemFirmwareUpdate")
        summit_rcm_plugins.append("modemEnable")
    except ImportError:
        PositioningSwitch = None

    if PositioningSwitch:
        try:
            add_route("/positioning", Positioning())
            add_route("/positioningSwitch", PositioningSwitch())
            add_route("/modemFirmwareUpdate", ModemFirmwareUpdate())
            add_route("/modemEnable", ModemEnable())
        except Exception as exception:
            syslog(LOG_ERR, f"Could not load modem endpoints - {str(exception)}")
            raise exception


async def add_radio_siso_mode_legacy():
    """Add the /radioSISOMode legacy route, if enabled"""
    try:
        from summit_rcm.radio_siso_mode.radio_siso_mode_service import (
            RadioSISOModeService,
        )
        from summit_rcm.rest_api.legacy.radio_siso_mode import (
            RadioSISOModeResourceLegacy,
        )

        summit_rcm_plugins.append("radioSISOMode")
    except ImportError:
        RadioSISOModeService = None
        RadioSISOModeResourceLegacy = None

    if RadioSISOModeService and RadioSISOModeResourceLegacy:
        try:
            add_route("/radioSISOMode", RadioSISOModeResourceLegacy())
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Could not load Radio SISO mode control endpoint - {str(exception)}",
            )
            raise exception


async def add_ntp_legacy():
    """
    Add the following legacy routes, if enabled:
    - /ntp
    - /ntp/{command}
    """
    try:
        from summit_rcm.chrony.ntp import NTP

        summit_rcm_plugins.append("ntp")
    except ImportError:
        NTP = None

    if NTP:
        try:
            add_route("/ntp", NTP())
            add_route("/ntp/{command}", NTP())
        except Exception as exception:
            syslog(LOG_ERR, f"Could not load NTP endpoints - {str(exception)}")
            raise exception


async def add_bluetooth_legacy():
    """
    Add the following legacy routes, if enabled, and determine if websockets access should require a
    valid, authenticated session:
    - /bluetooth/{controller}
    - /bluetooth/{controller}/{device}
    """
    try:
        # Note: Authenticating websocket users by header token is non-standard; an alternative
        # method may be required for Javascript browser clients.

        from summit_rcm.bluetooth.bt import Bluetooth
        from summit_rcm.bluetooth.bt_ble import websockets_auth_by_header_token

        summit_rcm_plugins.append("bluetooth")

        if Bluetooth and websockets_auth_by_header_token:
            summit_rcm_plugins.append("ws")
    except ImportError:
        Bluetooth = None

    if Bluetooth:
        try:
            bluetooth = Bluetooth()
            await bluetooth.setup(app)

            add_route("/bluetooth/{controller}", bluetooth, suffix="no_device")
            add_route("/bluetooth/{controller}/{device}", bluetooth)
        except Exception as exception:
            syslog(LOG_ERR, f"Could not load Bluetooth endpoints - {str(exception)}")
            raise exception


async def add_system_v2():
    """
    Add the following v2 routes, if enabled:
    - /api/v2/system/power
    - /api/v2/system/update
    - /api/v2/system/update/updatefile
    - /api/v2/system/fips
    - /api/v2/system/factoryReset
    - /api/v2/system/datetime
    - /api/v2/system/config/import
    - /api/v2/system/config/export
    - /api/v2/system/logs/export
    - /api/v2/system/debug/export
    """
    try:
        from summit_rcm.rest_api.v2.system.power import PowerResource
        from summit_rcm.rest_api.v2.system.update import (
            FirmwareUpdateStatusResource,
            FirmwareUpdateFileResource,
        )
        from summit_rcm.rest_api.v2.system.fips import FipsResource
        from summit_rcm.rest_api.v2.system.factory_reset import FactoryResetResource
        from summit_rcm.rest_api.v2.system.date_time import DateTimeResource
        from summit_rcm.rest_api.v2.system.config import (
            SystemConfigImportResource,
            SystemConfigExportResource,
        )
        from summit_rcm.rest_api.v2.system.logs import LogsExportResource
        from summit_rcm.rest_api.v2.system.debug import DebugExportResource
    except ImportError:
        PowerResource = None

    if PowerResource:
        try:
            add_route("/api/v2/system/power", PowerResource())
            add_route("/api/v2/system/update", FirmwareUpdateStatusResource())
            add_route("/api/v2/system/update/updateFile", FirmwareUpdateFileResource())
            add_route("/api/v2/system/fips", FipsResource())
            add_route("/api/v2/system/factoryReset", FactoryResetResource())
            add_route("/api/v2/system/datetime", DateTimeResource())
            await DateTimeService().populate_time_zone_list()
            add_route("/api/v2/system/config/import", SystemConfigImportResource())
            add_route("/api/v2/system/config/export", SystemConfigExportResource())
            add_route("/api/v2/system/logs/export", LogsExportResource())
            add_route("/api/v2/system/debug/export", DebugExportResource())
        except Exception as exception:
            syslog(LOG_ERR, f"Could not load system endpoints - {str(exception)}")
            raise exception


def add_middleware(enable_session_checking: bool) -> None:
    """Add middleware to the ASGI application"""
    # Add ASGI lifespan middleware
    app.add_middleware(LifespanMiddleware())

    # Add middleware to force session checking if enabled
    if enable_session_checking:
        from summit_rcm.sessions_middleware import SessionsMiddleware

        app.add_middleware(SessionsMiddleware())
        app.add_middleware(SessionCheckingMiddleware())

    # Add middleware to inject secure headers
    app.add_middleware(SecureHeadersMiddleware())


async def add_routes() -> None:
    """Add routes to the ASGI application"""
    await asyncio.gather(
        # v2 routes
        add_network_v2(),
        add_system_v2(),
        # legacy routes
        add_network_legacy(),
        add_firewall_legacy(),
        add_firmware_legacy(),
        add_definitions_legacy(),
        add_users_legacy(),
        add_version_legacy(),
        add_advanced_legacy(),
        add_files_legacy(),
        add_certificates_legacy(),
        add_logs_legacy(),
        add_unauthenticated_legacy(),
        add_awm_legacy(),
        add_stunnel_legacy(),
        add_modem_legacy(),
        add_date_time_legacy(),
        add_ntp_legacy(),
        add_bluetooth_legacy(),
        add_radio_siso_mode_legacy(),
    )


def add_route(route_path: str, resource: Any, **kwargs):
    """Add a route to the app and log it"""
    app.add_route(uri_template=route_path, resource=resource, kwargs=kwargs)
    syslog(f"route loaded: {str(route_path)}")


def start_server():
    """Start the webserver and add middleware"""
    parser = ServerConfig().get_parser()
    enable_sessions = parser.getboolean(
        section="/", option="tools.sessions.on", fallback=True
    )

    add_middleware(enable_sessions)


# Configure logging and start the application
openlog("summit-rcm")
syslog("Starting webserver")
start_server()
