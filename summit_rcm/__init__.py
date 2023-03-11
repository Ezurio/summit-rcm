from syslog import LOG_ERR, syslog
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
import asyncio
import uvicorn
import falcon.asgi
import ssl

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


# class SessionCheckingMiddleware:
#     def __init__(self) -> None:
#         self.paths = [
#             "connections",
#             "connection",
#             "accesspoints",
#             "allowUnauthenticatedResetReboot",
#             "networkInterfaces",
#             "networkInterface",
#             "file",
#             "users",
#             "firmware",
#             "logData",
#             "logSetting",
#             "logForwarding",
#             "poweroff",
#             "suspend",
#             "files",
#             "certificates",
#             "datetime",
#             "fips",
#             "modemEnable",
#         ]

#         if not AllowUnauthenticatedResetReboot().allow_unauthenticated_reset_reboot:
#             self.paths += ["factoryReset", "reboot"]

#         # if Bluetooth and websockets_auth_by_header_token:
#         #     self.paths.append("ws")

#     def process_request(self, req, resp):
#         """
#         Raise HTTP 401 Unauthorized client error if a session with invalid id tries to access
#         following resources. HTMLs still can be loaded to keep consistency, i.e. loaded from local
#         cache or remotely.
#         """
#         # # Check if SSL client authentication is enabled and if it failed ('SSL_CLIENT_VERIFY' is
#         # # 'SUCCESS' when authentication is successful).
#         # if (
#         #     cherrypy.request.app.config["summit-rcm"].get("enable_client_auth", False)
#         #     and cherrypy.request.wsgi_environ.get("SSL_CLIENT_VERIFY", "NONE") != "SUCCESS"
#         # ):
#         #     # Could not authenticate client
#         #     raise cherrypy.HTTPError(401)

#         # With the `get` method the session id will be saved which could result in session fixation vulnerability.
#         # Session ids will be destroyed periodically so we have to check 'USERNAME' to make sure the session is not valid after logout.
#         # if not cherrypy.session._exists() or not cherrypy.session.get("USERNAME", None):
#         if not req.get_cookie_values("USERNAME"):
#             url = req.url.split("/")[-1]
#             path_root = req.path.split("/")[1]
#             if (
#                 url
#                 and ".html" not in url
#                 and ".js" not in url
#                 and (path_root in self.paths or path_root in summit_rcm_plugins)
#             ):
#                 resp.status = falcon.HTTP_401
#                 resp.complete = True


class IndexResource(object):
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_TEXT
        resp.text = "Summit RCM"


# class FaviconResource(object):
#     async def on_get(self, req, resp):
#         resp.status = falcon.HTTP_200
#         resp.content_type = falcon.MEDIA_PNG
#         with open("/var/www/assets/img/favicon.png", "rb") as f:
#             resp.text = f.read()


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


async def add_static_routes():
    # static_dir: str = (
    #     ServerConfig()
    #     .get_parser()
    #     .get("/", "tools.staticdir.dir", fallback="/var/www")
    #     .strip('"')
    # )
    # app.add_static_route("/", static_dir)
    app.add_route("/", IndexResource())
    # app.add_route("/favicon.ico", FaviconResource())
    syslog("__main__: static routes loaded")


async def add_definitions():
    app.add_route("/definitions", DefinitionsResource())
    syslog("__main__: definitions route loaded")


async def add_firewall():
    if Firewall:
        firewall = Firewall()

        app.add_route("/firewall", firewall)
        app.add_route("/firewall/{command}", firewall)
        syslog("__main__: firewall loaded")
    else:
        syslog("__main__: firewall NOT loaded")


async def add_users():
    try:
        login_manage = LoginManage()
        user_manage = UserManage()

        app.add_route("/login", login_manage)
        app.add_route("/users", user_manage)
        syslog("__main__: users loaded")
    except ImportError:
        syslog("__main__: users NOT loaded")


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
        syslog("__main__: network loaded")
    except ImportError:
        syslog("__main__: network NOT loaded")


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
        syslog("__main__: advanced loaded")
    except ImportError:
        syslog("__main__: advanced NOT loaded")


async def add_certificates():
    try:
        certs = Certificates()

        app.add_route("/certificates", certs)
        syslog("__main__: certificates loaded")
    except ImportError:
        syslog("__main__: certificates NOT loaded")


async def add_files():
    try:
        file_manage = FileManage()
        files_manage = FilesManage()

        app.add_route("/files", files_manage)
        app.add_route("/file", file_manage)
        syslog("__main__: files loaded")
    except ImportError:
        syslog("__main__: files NOT loaded")


async def add_date_time():
    try:
        date_time_setting = DateTimeSetting()

        app.add_route("/datetime", date_time_setting)
        await date_time_setting.populate_time_zone_list()
        syslog("__main__: datetime loaded")
    except ImportError:
        syslog("__main__: datetime NOT loaded")


async def add_logs():
    try:
        log_data = LogData()
        log_setting = LogSetting()
        log_forwarding = LogForwarding()

        app.add_route("/logData", log_data)
        app.add_route("/logSetting", log_setting)
        app.add_route("/logForwarding", log_forwarding)
        syslog("__main__: logs loaded")
    except ImportError:
        syslog("__main__: logs NOT loaded")


async def add_version():
    try:
        version = Version()

        app.add_route("/version", version)
        syslog("__main__: version loaded")
    except ImportError:
        syslog("__main__: version NOT loaded")


async def add_firmware():
    try:
        swupdate = SWUpdate()

        app.add_route("/firmware", swupdate)
        syslog("__main__: firmware loaded")
    except ImportError:
        syslog("__main__: firmware NOT loaded")


async def add_unauthenticated():
    try:
        unauthenticated = AllowUnauthenticatedResetReboot()

        app.add_route("/allowUnauthenticatedResetReboot", unauthenticated)
        syslog("__main__: allowUnauthenticatedResetReboot loaded")
    except ImportError:
        syslog("__main__: allowUnauthenticatedResetReboot NOT loaded")


async def add_awm():
    if AWMCfgManage:
        awm = AWMCfgManage()

        app.add_route("/awm", awm)
        syslog("__main__: AWM loaded")
    else:
        syslog("__main__: AWM NOT loaded")


async def add_stunnel():
    if Stunnel:
        stunnel = Stunnel()

        app.add_route("/stunnel", stunnel)
        syslog("__main__: stunnel loaded")
    else:
        syslog("__main__: stunnel NOT loaded")


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
        syslog("__main__: modem loaded")
    else:
        syslog("__main__: modem NOT loaded")


async def add_radio_siso_mode():
    if RadioSISOMode:
        radioSISOMode = RadioSISOMode()

        app.add_route("/radioSISOMode", radioSISOMode)
        syslog("__main__: Radio SISO mode loaded")
    else:
        syslog("__main__: Radio SISO mode NOT loaded")


async def add_ntp():
    if NTP:
        ntp = NTP()

        app.add_route("/ntp", ntp)
        app.add_route("/ntp/{command}", ntp)
        syslog("__main__: chrony NTP loaded")
    else:
        syslog("__main__: chrony NTP NOT loaded")


async def add_bluetooth():
    if Bluetooth:
        bluetooth = Bluetooth()
        await bluetooth.setup()

        app.add_route("/bluetooth", bluetooth)
        syslog("__main__: Bluetooth loaded")
    else:
        syslog("__main__: Bluetooth NOT loaded")


def enable_ssl_client_auth(
    socket: ssl.SSLSocket, ssl_certificate_chain: str, ssl_private_key: str
) -> bool:
    """
    Enable SSL client authentication on the give SSL socket using the provided CA certificate chain
    and private key.
    """

    try:
        socket.context.load_cert_chain(ssl_certificate_chain, ssl_private_key)
        if ssl.OPENSSL_VERSION_NUMBER >= 0x10101000:
            # OpenSSL 1.1.1 or newer - we can use the built-in functionality to disable time
            # checking during certificate verification
            socket.context.verify_mode = ssl.CERT_REQUIRED
            socket.context.verify_flags |= X509_V_FLAG_NO_CHECK_TIME
        else:
            # OpenSSL 1.0.2 - we need to use the patched-in functionality to disable time
            # checking during certificate verification
            socket.context.verify_mode = PY_SSL_CERT_REQUIRED_NO_CHECK_TIME
        syslog("SSL client authentication enabled")
        return True
    except Exception as e:
        syslog(LOG_ERR, f"Error configuring SSL client authentication - {str(e)}")
        return False


def add_middleware(enable_session_checking: bool) -> None:
    # Add ASGI lifespan middleware
    app.add_middleware(LifespanMiddleware())

    # # Add middleware to force session checking if enabled
    # if enable_session_checking:
    #     app.add_middleware(SessionCheckingMiddleware())

    # Add middleware to inject secure headers
    app.add_middleware(SecureHeadersMiddleware())


async def add_routes() -> None:
    await add_network()
    await add_firewall()
    await add_firmware()
    # await add_static_routes()
    await add_definitions()
    await add_users()
    await add_version()
    await add_advanced()
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

    socket_host = (
        ServerConfig()
        .get_parser()
        .get("global", "server.socket_host", fallback="")
        .strip('"')
    )
    socket_port = parser.getint("global", "server.socket_port", fallback=443)
    ssl_private_key = (
        parser["global"]
        .get("server.ssl_private_key", "/etc/summit-rcm/ssl/server.key")
        .strip('"')
    )
    ssl_certificate = (
        parser["global"]
        .get("server.ssl_certificate", "/etc/summit-rcm/ssl/server.crt")
        .strip('"')
    )
    ssl_certificate_chain = (
        parser["global"]
        .get("server.ssl_certificate_chain", "/etc/summit-rcm/ssl/ca.crt")
        .strip('"')
    )
    enable_client_auth = parser.getboolean(
        section="summit-rcm", option="enable_client_auth", fallback=False
    )
    enable_sessions = parser.getboolean(
        section="/", option="tools.sessions.on", fallback=True
    )

    config = uvicorn.Config(
        app=app,
        host=socket_host,
        port=socket_port,
        # ssl_certfile=ssl_certificate,
        # ssl_keyfile=ssl_private_key,
        # ssl_cert_reqs=ssl.CERT_NONE,
        # ssl_ca_certs=ssl_certificate_chain,
        # ssl_version=ssl.PROTOCOL_SSLv23,
        lifespan="on",
        http="auto",
        loop="asyncio",
        log_level="error",
    )
    server = uvicorn.Server(config)

    add_middleware(enable_sessions)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(server.serve())


def main(args=None):
    syslog("Starting webserver")
    start_server()
