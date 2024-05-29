"""
Summit RCM main module
"""

import asyncio
import importlib
import pkgutil
from syslog import LOG_ERR, syslog, openlog
from types import ModuleType
from typing import Any, Iterable, List, Optional
import os

try:
    import ssl
except ImportError as error:
    # Ignore the error if the ssl module is not available if generating documentation
    if os.environ.get("DOCS_GENERATION") != "True":
        raise error

from summit_rcm.utils import Singleton
from summit_rcm.services.date_time_service import DateTimeService
from summit_rcm.rest_api.services.spectree_service import SpectreeService
from summit_rcm.settings import ServerConfig
from summit_rcm.definition import RouteAdd


try:
    import falcon.asgi

    try:
        import uvicorn.config
    except ImportError as error:
        # Ignore the error if the uvicorn module is not available if generating documentation
        if os.environ.get("DOCS_GENERATION") != "True":
            raise error

    app = falcon.asgi.App()
    REST_ENABLED = True

    PY_SSL_CERT_REQUIRED_NO_CHECK_TIME = 3
    """Custom OpenSSL verify mode to disable time checking during certificate verification"""

    X509_V_FLAG_NO_CHECK_TIME = 0x200000
    """Flags for OpenSSL 1.1.1 or newer to disable time checking during certificate verification"""

    summit_rcm_plugins: List[str] = []

    discovered_plugins: dict[str, ModuleType] = {}

    log_routes_loaded = (
        ServerConfig()
        .get_parser()
        .getboolean(section="summit-rcm", option="log_routes_loaded", fallback=False)
    )

    class SecureHeadersMiddleware:
        """Middleware that enables the use of secure headers"""

        async def process_response(self, req, resp, resource, req_succeeded):
            """Add secure headers to the response before it's returned to the client"""
            resp.set_header("X-Frame-Options", "DENY")
            resp.set_header("X-Content-Type-Options", "nosniff")
            resp.set_header(
                "Content-Security-Policy",
                "default-src "
                "'self' "
                "cdn.jsdelivr.net "
                "fonts.googleapis.com "
                "fonts.gstatic.com "
                "'unsafe-inline'",
            )
            # Add Strict-Transport headers
            resp.set_header("Strict-Transport-Security", "max-age=600")  # ten minutes

    class SessionCheckingMiddleware(metaclass=Singleton):
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
                "poweroff",
                "suspend",
                "files",
                "certificates",
                "datetime",
                "fips",
                "/api/v2/network/interfaces",
                "/api/v2/network/connections",
                "/api/v2/network/accessPoints",
                "/api/v2/network/certificates",
                "/api/v2/network/wifi",
                "/api/v2/system/power",
                "/api/v2/system/update",
                "/api/v2/system/fips",
                "/api/v2/system/factoryReset",
                "/api/v2/system/datetime",
                "/api/v2/system/config",
                "/api/v2/system/logs",
                "/api/v2/system/debug",
                "/api/v2/system/version",
                "/api/v2/login/users",
            ]

        def session_is_valid(self, req: falcon.asgi.Request) -> bool:
            """Determine if the current request's session is valid"""
            # With the `get` method the session id will be saved which could result in session
            # fixation vulnerability. Session ids will be destroyed periodically so we have to check
            # 'USERNAME' to make sure the session is not valid after logout.
            if not hasattr(req.context, "valid_session"):
                return False

            if not req.context.valid_session:
                return False

            username = req.context.get_session("USERNAME")
            return username is not None and username != ""

        def is_restricted_path(self, req: falcon.asgi.Request) -> bool:
            """Determine if the request's path belongs to a restricted resource"""
            url = req.url.split("/")[-1]

            if not url:
                return False

            if ".html" in url:
                return False

            if ".js" in url:
                return False

            path_root = req.path.split("/")[1]
            if path_root in self.paths or path_root in summit_rcm_plugins:
                return True

            # For v2 routes, check if the requested path starts with a restricted path string
            for path in self.paths:
                if req.path.startswith(path):
                    return True

            for plugin in summit_rcm_plugins:
                if req.path.startswith(plugin):
                    return True

            return False

        async def process_request(
            self, req: falcon.asgi.Request, resp: falcon.asgi.Response
        ):
            """
            Raise HTTP 401 Unauthorized client error if a session with invalid id tries to access
            restricted resources.
            """
            if self.session_is_valid(req):
                return

            # The current session is not valid (or there is no current session), so check if the
            # requested path is restricted
            if not self.is_restricted_path(req):
                return

            # The session is invalid and the requested path is restricted, so return an HTTP 401
            # Unauthorized error
            resp.status = falcon.HTTP_401
            resp.complete = True

        async def process_request_ws(
            self, req: falcon.asgi.Request, ws: falcon.asgi.WebSocket
        ):
            """
            Close a WebSocket connection if a session with invalid id tries to access restricted
            resources.
            """
            if self.session_is_valid(req):
                return

            # The current session is not valid (or there is no current session), so check if the
            # requested path is restricted
            if not self.is_restricted_path(req):
                return

            # The session is invalid and the requested path is restricted, so close the WebSocket
            await ws.close()

    class IndexResource:
        """Main index resource"""

        async def on_get(self, req, resp):
            """GET handler for / endpoint"""
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_TEXT
            resp.text = "Summit RCM"

    async def custom_handle_uncaught_exception(req, resp, exception, params):
        """Custom handler for uncaught errors"""

        syslog(
            LOG_ERR,
            f"Uncaught error - {str(exception)}, "
            f"req: {str(req)}, "
            f"resp: {str(resp)}, "
            f"params: {str(params)}",
        )
        raise exception

    async def add_definitions_legacy():
        """Add the legacy /definition route, if enabled"""
        try:
            from summit_rcm.rest_api.legacy.definitions import DefinitionsResource
        except ImportError:
            DefinitionsResource = None

        if DefinitionsResource:
            add_route("/definitions", DefinitionsResource())

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
                    LOG_ERR,
                    f"Could not load user management endpoints - {str(exception)}",
                )
                raise exception

    async def add_network_v2():
        """
        Add the following v2 routes, if enabled:
        - /api/v2/network/status
        - /api/v2/network/interfaces
        - /api/v2/network/interfaces/{name}
        - /api/v2/network/interfaces/{name}/stats
        - /api/v2/network/interfaces/{name}/driverInfo
        - /api/v2/network/connections
        - /api/v2/network/connections/uuid/{uuid}
        - /api/v2/network/connections/id/{id}
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
                NetworkInterfaceDriverInfoResource,
            )
            from summit_rcm.rest_api.v2.network.connections import (
                NetworkConnectionsResource,
                NetworkConnectionResourceByUuid,
                NetworkConnectionResourceById,
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
                if ServerConfig().get_parser().getboolean(
                    section="summit-rcm", option="network_status_restricted", fallback=False
                ):
                    SessionCheckingMiddleware().paths.append("/api/v2/network/status")
                add_route("/api/v2/network/interfaces", NetworkInterfacesResource())
                add_route(
                    "/api/v2/network/interfaces/{name}", NetworkInterfaceResource()
                )
                add_route(
                    "/api/v2/network/interfaces/{name}/stats",
                    NetworkInterfaceStatsResource(),
                )
                add_route(
                    "/api/v2/network/interfaces/{name}/driverInfo",
                    NetworkInterfaceDriverInfoResource(),
                )
                add_route("/api/v2/network/connections", NetworkConnectionsResource())
                add_route(
                    "/api/v2/network/connections/uuid/{uuid}",
                    NetworkConnectionResourceByUuid(),
                )
                add_route(
                    "/api/v2/network/connections/id/{id}",
                    NetworkConnectionResourceById(),
                )
                add_route(
                    "/api/v2/network/connections/import",
                    NetworkConnectionsImportResource(),
                )
                add_route(
                    "/api/v2/network/connections/export",
                    NetworkConnectionsExportResource(),
                )
                add_route("/api/v2/network/accessPoints", AccessPointsResource())
                add_route(
                    "/api/v2/network/accessPoints/scan", AccessPointsScanResource()
                )
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
        - /networkInterfaceDriverInfo
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
                NetworkInterfaceDriverInfo,
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
                if ServerConfig().get_parser().getboolean(
                    section="summit-rcm", option="network_status_restricted", fallback=False
                ):
                    SessionCheckingMiddleware().paths.append("networkStatus")
                add_route("/networkInterface", NetworkInterface())
                add_route("/networkInterfaces", NetworkInterfaces())
                add_route("/networkInterfaceStatistics", NetworkInterfaceStatistics())
                add_route("/networkInterfaceDriverInfo", NetworkInterfaceDriverInfo())
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
                summit_rcm_plugins.append("factoryReset")
                summit_rcm_plugins.append("reboot")
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
                syslog(
                    LOG_ERR, f"Could not load certificates endpoint - {str(exception)}"
                )
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
        """
        try:
            from summit_rcm.rest_api.legacy.log import LogData, LogSetting
        except ImportError:
            LogData = None

        if LogData:
            try:
                add_route("/logData", LogData())
                add_route("/logSetting", LogSetting())
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
                    LOG_ERR,
                    f"Could not load firmware update endpoint - {str(exception)}",
                )
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
        - /api/v2/system/datetime/ntp
        - /api/v2/system/datetime/ntp/{address}
        - /api/v2/system/config/import
        - /api/v2/system/config/export
        - /api/v2/system/logs/data
        - /api/v2/system/logs/config
        - /api/v2/system/logs/forwarding
        - /api/v2/system/logs/export
        - /api/v2/system/debug/export
        - /api/v2/system/version
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
            from summit_rcm.rest_api.v2.system.logs import (
                LogsDataResource,
                LogsConfigResource,
                LogsExportResource,
            )
            from summit_rcm.rest_api.v2.system.debug import DebugExportResource
            from summit_rcm.rest_api.v2.system.version import VersionResource

        except ImportError:
            PowerResource = None

        if PowerResource:
            try:
                add_route("/api/v2/system/power", PowerResource())
                add_route("/api/v2/system/update", FirmwareUpdateStatusResource())
                add_route(
                    "/api/v2/system/update/updateFile", FirmwareUpdateFileResource()
                )
                add_route("/api/v2/system/fips", FipsResource())
                add_route("/api/v2/system/factoryReset", FactoryResetResource())
                add_route("/api/v2/system/datetime", DateTimeResource())
                await DateTimeService().populate_time_zone_list()
                add_route("/api/v2/system/config/import", SystemConfigImportResource())
                add_route("/api/v2/system/config/export", SystemConfigExportResource())
                add_route("/api/v2/system/logs/data", LogsDataResource())
                add_route("/api/v2/system/logs/config", LogsConfigResource())
                add_route("/api/v2/system/logs/export", LogsExportResource())
                add_route("/api/v2/system/debug/export", DebugExportResource())
                add_route("/api/v2/system/version", VersionResource())
            except Exception as exception:
                syslog(LOG_ERR, f"Could not load system endpoints - {str(exception)}")
                raise exception

    async def add_login_v2():
        """
        Add the following v2 routes, if enabled:
        - /api/v2/login
        - /api/v2/login/users
        - /api/v2/login/users/{username}
        """
        try:
            from summit_rcm.rest_api.v2.login.login import LoginResource
            from summit_rcm.rest_api.v2.login.users import UsersResource
            from summit_rcm.rest_api.v2.login.users import UserResource
        except ImportError:
            LoginResource = None

        if LoginResource:
            try:
                add_route("/api/v2/login", LoginResource())
                add_route("/api/v2/login/users", UsersResource())
                add_route("/api/v2/login/users/{username}", UserResource())
            except Exception as exception:
                syslog(LOG_ERR, f"Could not load login endpoints - {str(exception)}")
                raise exception

    class LazyLoadRoutesMiddleware:
        """Middleware that lazy-loads routes"""

        legacy_network_routes = RouteAdd(add_network_legacy())
        legacy_users_routes = RouteAdd(add_users_legacy())
        legacy_advanced_routes = RouteAdd(add_advanced_legacy())
        legacy_files_routes = RouteAdd(add_files_legacy())
        legacy_logs_routes = RouteAdd(add_logs_legacy())

        routes_dict = {
            "/api/v2/network": RouteAdd(add_network_v2()),
            "/api/v2/system": RouteAdd(add_system_v2()),
            "/api/v2/login": RouteAdd(add_login_v2()),
            "/networkStatus": legacy_network_routes,
            "/networkInterface": legacy_network_routes,
            "/networkInterfaces": legacy_network_routes,
            "/connection": legacy_network_routes,
            "/connections": legacy_network_routes,
            "/accesspoints": legacy_network_routes,
            "/wifiEnable": legacy_network_routes,
            "/firmware": RouteAdd(add_firmware_legacy()),
            "/definitions": RouteAdd(add_definitions_legacy()),
            "/login": legacy_users_routes,
            "/users": legacy_users_routes,
            "/version": RouteAdd(add_version_legacy()),
            "/poweroff": legacy_advanced_routes,
            "/suspend": legacy_advanced_routes,
            "/reboot": legacy_advanced_routes,
            "/factoryReset": legacy_advanced_routes,
            "/fips": legacy_advanced_routes,
            "/files": legacy_files_routes,
            "/file": legacy_files_routes,
            "/certificates": RouteAdd(add_certificates_legacy()),
            "/logData": legacy_logs_routes,
            "/logSetting": legacy_logs_routes,
            "/datetime": RouteAdd(add_date_time_legacy()),
        }

        async def process_request(self, req, resp):
            """Load the routes when the first request is received"""
            global discovered_plugins

            # Check if the requested path is already loaded
            if app._router.find(req.path):
                return True

            # Check if the requested path is a known route and load it
            for route, route_add in self.routes_dict.items():
                if req.path.startswith(route):
                    if route_add.awaited:
                        break
                    await route_add.route
                    route_add.awaited = True
                    if app._router.find(req.path):
                        return True
                    break

            # Check if the requested path is a plugin route and load it
            for name, module in discovered_plugins.items():
                # If optional method for supported routes is implemented, use it
                if hasattr(module, "get_legacy_supported_routes") and hasattr(
                    module, "get_v2_supported_routes"
                ):
                    legacy_module_routes = await module.get_legacy_supported_routes()
                    v2_module_routes = await module.get_v2_supported_routes()
                else:
                    legacy_module_routes = await module.get_legacy_routes()
                    v2_module_routes = await module.get_v2_routes()

                for route in v2_module_routes:
                    if route == req.path:
                        if isinstance(v2_module_routes, list):
                            v2_module_routes_dict = await module.get_v2_routes()
                        else:
                            v2_module_routes_dict = v2_module_routes
                        for route in v2_module_routes_dict:
                            add_route(route, v2_module_routes_dict[route])
                            summit_rcm_plugins.append(route[1:])
                        return True

                for route in legacy_module_routes:
                    if route == req.path:
                        if isinstance(legacy_module_routes, list):
                            legacy_module_routes_dict = await module.get_legacy_routes()
                        else:
                            legacy_module_routes_dict = legacy_module_routes
                        for route in legacy_module_routes_dict:
                            add_route(route, legacy_module_routes_dict[route])
                            summit_rcm_plugins.append(route[1:])
                        return True

    def add_default_middleware() -> None:
        """Add middleware to the ASGI application"""

        # Add middleware to inject secure headers
        app.add_middleware(SecureHeadersMiddleware())

        # Add middleware to lazy-load routes
        app.add_middleware(LazyLoadRoutesMiddleware())

        # Add middleware to force session checking if enabled
        if ServerConfig().sessions_enabled:
            from summit_rcm.sessions_middleware import SessionsMiddleware

            app.add_middleware(SessionsMiddleware())
            app.add_middleware(SessionCheckingMiddleware())

        if ServerConfig().rest_api_docs_enabled:
            SpectreeService().register(app)

    def add_route(route_path: str, resource: Any, **kwargs):
        """Add a route to the app and log it"""
        app.add_route(uri_template=route_path, resource=resource, kwargs=kwargs)
        if log_routes_loaded:
            syslog(f"route loaded: {str(route_path)}")

    def discover_plugins(path: Optional[Iterable[str]] = None):
        """Discover all plugins"""
        global discovered_plugins

        discovered_plugins = {
            name: importlib.import_module(name)
            for finder, name, ispkg in pkgutil.iter_modules(path=path)
            if name.startswith("summit_rcm_")
        }

    async def start_server():
        """Start the webserver and add middleware"""
        global discovered_plugins

        syslog("Starting webserver")

        parser = ServerConfig().get_parser()
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
            .get(
                "server.ssl_certificate_chain",
                "/etc/summit-rcm/ssl/ca.crt",
            )
            .strip('"')
        )
        enable_client_auth = parser.getboolean(
            section="summit-rcm", option="enable_client_auth", fallback=False
        )
        disable_certificate_expiry_verification = parser.getboolean(
            section="summit-rcm",
            option="disable_certificate_expiry_verification",
            fallback=True,
        )
        port = parser.getint(section="summit-rcm", option="socket_port", fallback=443)

        websockets_config = "none"
        try:
            import websockets

            websockets_config = "websockets"
        except ImportError:
            pass

        config = uvicorn.Config(
            app=app,
            host="",
            port=port,
            ssl_certfile=ssl_certificate,
            ssl_keyfile=ssl_private_key,
            ssl_cert_reqs=ssl.CERT_NONE,
            ssl_ca_certs=ssl_certificate_chain,
            ssl_version=ssl.PROTOCOL_TLS_SERVER,
            lifespan="on",
            http="auto",
            loop="asyncio",
            log_level="error",
            ws=websockets_config,
        )

        # Populate the list of discovered plugins
        discover_plugins()

        # Call any plugin config pre-load hooks
        for name, module in discovered_plugins.items():
            try:
                await module.server_config_preload_hook(config)
            except Exception as exception:
                syslog(
                    LOG_ERR,
                    f"Error in plugin {name} config pre-load hook: {str(exception)}",
                )

        # Load the Uvicorn server config
        config.load()

        # Update Uvicorn server's SSL context configuration to require client authentication and
        # certificate expiration validation if enabled
        if enable_client_auth:
            try:
                if ssl.OPENSSL_VERSION_NUMBER >= 0x10101000:
                    # OpenSSL 1.1.1 or newer - we can use the built-in functionality to disable time
                    # checking during certificate verification, only if enabled
                    config.ssl.verify_mode = ssl.CERT_REQUIRED
                    if disable_certificate_expiry_verification:
                        config.ssl.verify_flags |= X509_V_FLAG_NO_CHECK_TIME
                else:
                    # OpenSSL 1.0.2 - we need to use the patched-in functionality to disable time
                    # checking during certificate verification, only if enabled
                    config.ssl.verify_mode = (
                        PY_SSL_CERT_REQUIRED_NO_CHECK_TIME
                        if disable_certificate_expiry_verification
                        else ssl.CERT_REQUIRED
                    )
            except Exception as exception:
                syslog(
                    LOG_ERR,
                    f"Error configuring SSL client authentication - {str(exception)}",
                )

        # Call any plugin config post-load hooks
        for name, module in discovered_plugins.items():
            try:
                await module.server_config_postload_hook(config)
            except Exception as exception:
                syslog(
                    LOG_ERR,
                    f"Error in plugin {name} config post-load hook: {str(exception)}",
                )

        if config.ssl.verify_mode == ssl.CERT_REQUIRED:
            syslog("SSL client authentication enabled")

        server = uvicorn.Server(config)

        # Add any middleware
        add_default_middleware()
        for name, module in discovered_plugins.items():
            try:
                app.add_middleware(await module.get_middleware())
            except Exception as exception:
                syslog(
                    LOG_ERR,
                    f"Error loading middleware for plugin {name}: {str(exception)}",
                )

        # Register uncaught exception handler
        app.add_error_handler(Exception, custom_handle_uncaught_exception)

        # Start serving
        await server.serve()

except ImportError:
    REST_ENABLED = False

# If enabled, load the AT interface
try:
    from summit_rcm.at_interface.at_interface import ATInterface

    async def start_at_interface():
        """Start the AT interface"""
        syslog("Starting AT interface")
        await ATInterface().start()

        if not REST_ENABLED:
            # If just the AT interface is running, we need to await a Future in order to prevent the
            # event loop from exiting
            await asyncio.get_event_loop().create_future()

except ImportError:
    ATInterface = None


async def start():
    """Configure logging and start the application"""
    openlog("summit-rcm")

    if not ATInterface and not REST_ENABLED:
        syslog(LOG_ERR, "Invalid configuration!")
        exit(1)

    tasks = []

    if ATInterface:
        tasks.append(asyncio.create_task(start_at_interface()))
    if REST_ENABLED:
        tasks.append(asyncio.create_task(start_server()))

    await asyncio.gather(*tasks)


def main():
    """Main entry point"""
    asyncio.run(start())
