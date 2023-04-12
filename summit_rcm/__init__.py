from syslog import syslog
from typing import List
from . import definition
from .network_status import NetworkStatus
from .network import (
    NetworkInterfaces,
    NetworkInterface,
    NetworkInterfaceStatistics,
    NetworkConnections,
    NetworkConnection,
    NetworkAccessPoints,
    WifiEnable,
)

from .log import LogData, LogSetting, LogForwarding

from .swupdate import SWUpdate
from .unauthenticated import AllowUnauthenticatedResetReboot
from .users import UserManage, LoginManage
from .files import FileManage, FilesManage
from .certificates import Certificates
from .advanced import PowerOff, Suspend, Reboot, FactoryReset, Fips
from .date_time import DateTimeSetting
from .settings import SystemSettingsManage, ServerConfig
from .version import Version
import falcon.asgi
from summit_rcm.rest_api.system.power import PowerResource

summit_rcm_plugins: List[str] = []

PY_SSL_CERT_REQUIRED_NO_CHECK_TIME = 3
"""
Custom OpenSSL verify mode to disable time checking during certificate verification
"""

X509_V_FLAG_NO_CHECK_TIME = 0x200000
"""
Flags for OpenSSL 1.1.1 or newer to disable time checking during certificate verification
"""

"""
Note: Authenticating websocket users by header token is non-standard; an alternative method
may be required for Javascript browser clients.
"""

try:
    from .bluetooth.bt import Bluetooth
    from .bluetooth.bt_ble import websockets_auth_by_header_token

    summit_rcm_plugins.append("bluetooth")
except ImportError:
    Bluetooth = None

try:
    from .awm.awm_cfg_manage import AWMCfgManage

    summit_rcm_plugins.append("awm")
except ImportError:
    AWMCfgManage = None

try:
    from .stunnel.stunnel import Stunnel

    summit_rcm_plugins.append("stunnel")
except ImportError:
    Stunnel = None

try:
    from .modem.modem import (
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

try:
    from .iptables.firewall import Firewall

    summit_rcm_plugins.append("firewall")
except ImportError:
    Firewall = None

try:
    from .radio_siso_mode.radio_siso_mode import RadioSISOMode

    summit_rcm_plugins.append("radioSISOMode")
except ImportError:
    RadioSISOMode = None

try:
    from .chrony.ntp import NTP

    summit_rcm_plugins.append("ntp")
except ImportError:
    NTP = None

try:
    from .at_interface.at_interface import ATInterface
except ImportError:
    ATInterface = None

app = falcon.asgi.App()


class SecureHeadersMiddleware:
    async def process_response(self, req, resp, resource, req_succeeded):
        headers = resp.headers
        headers["X-Frame-Options"] = "DENY"
        headers["X-XSS-Protection"] = "1; mode=block"
        headers["X-Content-Type-Options"] = "nosniff"
        headers["Content-Security-Policy"] = "default-src 'self'"
        # Add Strict-Transport headers
        headers["Strict-Transport-Security"] = "max-age=31536000"  # one year


class LifespanMiddleware:
    async def process_startup(self, scope, event):
        await add_routes()


class SessionCheckingMiddleware:
    def __init__(self) -> None:
        self.paths = [
            "connections",
            "connection",
            "accesspoints",
            "allowUnauthenticatedResetReboot",
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

        if not AllowUnauthenticatedResetReboot().allow_unauthenticated_reset_reboot:
            self.paths += ["factoryReset", "reboot"]

        if Bluetooth and websockets_auth_by_header_token:
            self.paths.append("ws")

    def session_is_valid(self, req) -> bool:
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


class IndexResource(object):
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_TEXT
        resp.text = "Summit RCM"


class DefinitionsResource(object):
    async def on_get(self, req, resp):
        plugins = []
        for k in ServerConfig().get_parser().options("plugins"):
            plugins.append(k)
        plugins.sort()

        settings = {}
        # If sessions aren't enabled, set the session_timeout to -1 to alert the frontend that we
        # don't need to auto log out.
        settings["session_timeout"] = (
            SystemSettingsManage.get_session_timeout()
            if ServerConfig()
            .get_parser()
            .getboolean("/", "tools.sessions.on", fallback=True)
            else -1
        )

        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        resp.media = {
            "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "",
            "Definitions": {
                "SDCERR": definition.SUMMIT_RCM_ERRORS,
                "PERMISSIONS": definition.USER_PERMISSION_TYPES,
                "DEVICE_TYPES": definition.SUMMIT_RCM_DEVTYPE_TEXT,
                "DEVICE_STATES": definition.SUMMIT_RCM_STATE_TEXT,
                "PLUGINS": plugins,
                "SETTINGS": settings,
            },
        }


async def add_definitions():
    app.add_route("/definitions", DefinitionsResource())
    syslog("definitions loaded")


async def add_firewall():
    if Firewall:
        firewall = Firewall()

        app.add_route("/firewall", firewall)
        app.add_route("/firewall/{command}", firewall)
        syslog("firewall loaded")
    else:
        syslog("firewall NOT loaded")


async def add_users():
    try:
        login_manage = LoginManage()
        user_manage = UserManage()

        app.add_route("/login", login_manage)
        app.add_route("/users", user_manage)
        syslog("users loaded")
    except ImportError:
        syslog("users NOT loaded")


async def add_network():
    try:
        status = NetworkStatus()
        await status.start()
        network_interface = NetworkInterface()
        network_interfaces = NetworkInterfaces()
        network_interface_stats = NetworkInterfaceStatistics()
        connections = NetworkConnections()
        connection = NetworkConnection()
        access_points = NetworkAccessPoints()
        wifi_enable = WifiEnable()

        app.add_route("/networkStatus", status)
        app.add_route("/networkInterface", network_interface)
        app.add_route("/networkInterfaces", network_interfaces)
        app.add_route("/networkInterfaceStatistics", network_interface_stats)
        app.add_route("/connections", connections)
        app.add_route("/connection", connection)
        app.add_route("/accesspoints", access_points)
        app.add_route("/wifiEnable", wifi_enable)
        syslog("network loaded")
    except ImportError:
        syslog("network NOT loaded")


async def add_advanced():
    try:
        power_off = PowerOff()
        suspend = Suspend()
        reboot = Reboot()
        factory_reset = FactoryReset()
        fips = Fips()

        app.add_route("/poweroff", power_off)
        app.add_route("/suspend", suspend)
        app.add_route("/reboot", reboot)
        app.add_route("/factoryReset", factory_reset)
        app.add_route("/fips", fips)
        syslog("advanced loaded")
    except ImportError:
        syslog("advanced NOT loaded")


async def add_certificates():
    try:
        certs = Certificates()

        app.add_route("/certificates", certs)
        syslog("certificates loaded")
    except ImportError:
        syslog("certificates NOT loaded")


async def add_files():
    try:
        file_manage = FileManage()
        files_manage = FilesManage()

        app.add_route("/files", files_manage)
        app.add_route("/file", file_manage)
        syslog("files loaded")
    except ImportError:
        syslog("files NOT loaded")


async def add_date_time():
    try:
        date_time_setting = DateTimeSetting()

        app.add_route("/datetime", date_time_setting)
        await date_time_setting.populate_time_zone_list()
        syslog("datetime loaded")
    except ImportError:
        syslog("datetime NOT loaded")


async def add_logs():
    try:
        log_data = LogData()
        log_setting = LogSetting()
        log_forwarding = LogForwarding()

        app.add_route("/logData", log_data)
        app.add_route("/logSetting", log_setting)
        app.add_route("/logForwarding", log_forwarding)
        syslog("logs loaded")
    except ImportError:
        syslog("logs NOT loaded")


async def add_version():
    try:
        version = Version()

        app.add_route("/version", version)
        syslog("version loaded")
    except ImportError:
        syslog("version NOT loaded")


async def add_firmware():
    try:
        swupdate = SWUpdate()

        app.add_route("/firmware", swupdate)
        syslog("firmware loaded")
    except ImportError:
        syslog("firmware NOT loaded")


async def add_unauthenticated():
    try:
        unauthenticated = AllowUnauthenticatedResetReboot()

        app.add_route("/allowUnauthenticatedResetReboot", unauthenticated)
        syslog("allowUnauthenticatedResetReboot loaded")
    except ImportError:
        syslog("allowUnauthenticatedResetReboot NOT loaded")


async def add_awm():
    if AWMCfgManage:
        awm = AWMCfgManage()

        app.add_route("/awm", awm)
        syslog("AWM loaded")
    else:
        syslog("AWM NOT loaded")


async def add_stunnel():
    if Stunnel:
        stunnel = Stunnel()

        app.add_route("/stunnel", stunnel)
        syslog("stunnel loaded")
    else:
        syslog("stunnel NOT loaded")


async def add_modem():
    if PositioningSwitch:
        positioning = Positioning()
        positioning_switch = PositioningSwitch()
        modem_firmware_update = ModemFirmwareUpdate()
        modem_enable = ModemEnable()

        app.add_route("/positioning", positioning)
        app.add_route("/positioningSwitch", positioning_switch)
        app.add_route("/modemFirmwareUpdate", modem_firmware_update)
        app.add_route("/modemEnable", modem_enable)
        syslog("modem loaded")
    else:
        syslog("modem NOT loaded")


async def add_radio_siso_mode():
    if RadioSISOMode:
        radioSISOMode = RadioSISOMode()

        app.add_route("/radioSISOMode", radioSISOMode)
        syslog("Radio SISO mode loaded")
    else:
        syslog("Radio SISO mode NOT loaded")


async def add_ntp():
    if NTP:
        ntp = NTP()

        app.add_route("/ntp", ntp)
        app.add_route("/ntp/{command}", ntp)
        syslog("chrony NTP loaded")
    else:
        syslog("chrony NTP NOT loaded")


async def add_bluetooth():
    if Bluetooth:
        bluetooth = Bluetooth()
        await bluetooth.setup()

        app.add_route("/bluetooth", bluetooth)
        syslog("Bluetooth loaded")
    else:
        syslog("Bluetooth NOT loaded")


async def add_system():
    app.add_route("/api/v2/system/power", PowerResource())
    syslog("/api/v2/system/power loaded")


def add_middleware(enable_session_checking: bool) -> None:
    # Add ASGI lifespan middleware
    app.add_middleware(LifespanMiddleware())

    # Add middleware to force session checking if enabled
    if enable_session_checking:
        from .sessions_middleware import SessionsMiddleware

        app.add_middleware(SessionsMiddleware())
        app.add_middleware(SessionCheckingMiddleware())

    # Add middleware to inject secure headers
    app.add_middleware(SecureHeadersMiddleware())


async def add_routes() -> None:
    await add_network()
    await add_firewall()
    await add_firmware()
    await add_definitions()
    await add_users()
    await add_version()
    await add_advanced()
    await add_system()
    await add_files()
    await add_certificates()
    await add_logs()
    await add_unauthenticated()
    await add_awm()
    await add_stunnel()
    await add_modem()
    await add_date_time()
    await add_ntp()
    await add_bluetooth()
    await add_radio_siso_mode()


def start_server():
    parser = ServerConfig().get_parser()
    enable_sessions = parser.getboolean(
        section="/", option="tools.sessions.on", fallback=True
    )

    add_middleware(enable_sessions)


syslog("Starting webserver")
start_server()

if ATInterface:
    syslog("Starting AT interface")
    ATInterface().start()
