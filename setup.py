#!/usr/bin/python
#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#

import glob
import os

from setuptools import setup, Extension

MYDIR = os.path.abspath(os.path.dirname(__file__))

try:
    from Cython.Distutils import build_ext

    CYTHON = True
except ImportError:
    CYTHON = False


class BuildFailed(Exception):
    pass


openssl_extension_module = Extension(
    "openssl_extension",
    libraries=["ssl", "crypto"],
    sources=["extensions/openssl/openssl_extension.c"],
)

packages = ["summit_rcm"]
environment_variable_value = os.environ.get("SUMMIT_RCM_EXTRA_PACKAGES", "")
if len(environment_variable_value) > 0:
    extra_packages = [s.strip() for s in environment_variable_value.split()]
else:
    extra_packages = []
for package in extra_packages:
    packages.append(package)


def get_cython_options():
    from distutils.errors import (
        CCompilerError,
        DistutilsExecError,
        DistutilsPlatformError,
    )

    ext_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError)

    class ve_build_ext(build_ext):
        # This class allows Cython building to fail.

        def run(self):
            try:
                super().run()
            except DistutilsPlatformError:
                raise BuildFailed()

        def build_extension(self, ext):
            try:
                super().build_extension(ext)
            except ext_errors as e:
                raise BuildFailed() from e
            except ValueError as e:
                # this can happen on Windows 64 bit, see Python issue 7511
                if "'path'" in str(e):
                    raise BuildFailed() from e
                raise

    def list_modules(dirname, pattern):
        filenames = glob.glob(os.path.join(dirname, pattern))

        module_names = []
        for name in filenames:
            module, ext = os.path.splitext(os.path.basename(name))
            if module != "__init__":
                module_names.append((module, ext))

        return module_names

    package_names = [p.replace("/", ".") for p in packages]

    modules_to_exclude = [
        "summit_rcm.rest_api.utils.spectree.models",
        "summit_rcm.rest_api.utils.spectree.tags",
        "summit_rcm.rest_api.utils.spectree.falcon_asgi_plugin",
        "summit_rcm.rest_api.services.spectree_service",
    ]

    cython_package_names = frozenset([])

    ext_modules = [
        Extension(
            package + "." + module,
            [os.path.join(*(package.split(".") + [module + ext]))],
        )
        for package in package_names
        for module, ext in list_modules(
            os.path.join(MYDIR, *package.split(".")),
            ("*.pyx" if package in cython_package_names else "*.py"),
        )
        if (package + "." + module) not in modules_to_exclude
    ]
    ext_modules.append(openssl_extension_module)

    for ext_mod in ext_modules:
        ext_mod.cython_directives = {
            "language_level": "3",
            "always_allow_keywords": True,
        }

    cmdclass = {"build_ext": ve_build_ext}
    return cmdclass, ext_modules


def generate_docs():
    from summit_rcm.rest_api.utils.spectree.generate_api_spec import generate_api_spec

    routes = {}

    try:
        from summit_rcm.rest_api.legacy.definitions import DefinitionsResource

        routes["/definitions"] = DefinitionsResource
    except ImportError:
        pass

    try:
        from summit_rcm.rest_api.legacy.users import UserManage, LoginManage

        routes["/login"] = LoginManage
        routes["/users"] = UserManage
    except ImportError:
        pass

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

        routes["/api/v2/network/status"] = NetworkStatusResource
        routes["/api/v2/network/interfaces"] = NetworkInterfacesResource
        routes["/api/v2/network/interfaces/{name}"] = NetworkInterfaceResource
        routes["/api/v2/network/interfaces/{name}/stats"] = (
            NetworkInterfaceStatsResource
        )
        routes["/api/v2/network/interfaces/{name}/driverInfo"] = (
            NetworkInterfaceDriverInfoResource
        )
        routes["/api/v2/network/connections"] = NetworkConnectionsResource
        routes["/api/v2/network/connections/uuid/{uuid}"] = (
            NetworkConnectionResourceByUuid
        )
        routes["/api/v2/network/connections/id/{id}"] = NetworkConnectionResourceById
        routes["/api/v2/network/connections/import"] = NetworkConnectionsImportResource
        routes["/api/v2/network/connections/export"] = NetworkConnectionsExportResource
        routes["/api/v2/network/accessPoints"] = AccessPointsResource
        routes["/api/v2/network/accessPoints/scan"] = AccessPointsScanResource
        routes["/api/v2/network/certificates"] = CertificatesResource
        routes["/api/v2/network/certificates/{name}"] = CertificateResource
        routes["/api/v2/network/wifi"] = WiFiResource
    except ImportError:
        pass

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

        routes["/networkStatus"] = NetworkStatus
        routes["/networkInterface"] = NetworkInterface
        routes["/networkInterfaces"] = NetworkInterfaces
        routes["/networkInterfaceStatistics"] = NetworkInterfaceStatistics
        routes["/networkInterfaceDriverInfo"] = NetworkInterfaceDriverInfo
        routes["/connections"] = NetworkConnections
        routes["/connection"] = NetworkConnection
        routes["/accesspoints"] = NetworkAccessPoints
        routes["/wifiEnable"] = WifiEnable
    except ImportError:
        pass

    try:
        from summit_rcm.rest_api.legacy.advanced import (
            PowerOff,
            Suspend,
            Reboot,
            FactoryReset,
            Fips,
        )

        routes["/poweroff"] = PowerOff
        routes["/suspend"] = Suspend
        routes["/reboot"] = Reboot
        routes["/factoryReset"] = FactoryReset
        routes["/fips"] = Fips
    except ImportError:
        pass

    try:
        from summit_rcm.rest_api.legacy.certificates import Certificates

        routes["/certificates"] = Certificates
    except ImportError:
        pass

    try:
        from summit_rcm.rest_api.legacy.files import FileManage, FilesManage

        routes["/files"] = FilesManage
        routes["/file"] = FileManage
    except ImportError:
        pass

    try:
        from summit_rcm.rest_api.legacy.date_time import DateTimeSetting

        routes["/datetime"] = DateTimeSetting
    except ImportError:
        pass

    try:
        from summit_rcm.rest_api.legacy.log import (
            LogData,
            LogSetting,
            LogsWebserverResourceLegacy,
        )

        routes["/logData"] = LogData
        routes["/logSetting"] = LogSetting
        routes["/logWebserver"] = LogsWebserverResourceLegacy
    except ImportError:
        pass

    try:
        from summit_rcm.rest_api.legacy.version import Version

        routes["/version"] = Version
    except ImportError:
        pass

    try:
        from summit_rcm.rest_api.legacy.swupdate import SWUpdate

        routes["/firmware"] = SWUpdate
    except ImportError:
        pass

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
            LogsWebserverResource,
        )
        from summit_rcm.rest_api.v2.system.debug import DebugExportResource
        from summit_rcm.rest_api.v2.system.version import VersionResource

        routes["/api/v2/system/power"] = PowerResource
        routes["/api/v2/system/update"] = FirmwareUpdateStatusResource
        routes["/api/v2/system/update/updateFile"] = FirmwareUpdateFileResource
        routes["/api/v2/system/fips"] = FipsResource
        routes["/api/v2/system/factoryReset"] = FactoryResetResource
        routes["/api/v2/system/datetime"] = DateTimeResource
        routes["/api/v2/system/config/import"] = SystemConfigImportResource
        routes["/api/v2/system/config/export"] = SystemConfigExportResource
        routes["/api/v2/system/logs/data"] = LogsDataResource
        routes["/api/v2/system/logs/config"] = LogsConfigResource
        routes["/api/v2/system/logs/export"] = LogsExportResource
        routes["/api/v2/system/logs/webserver"] = LogsWebserverResource
        routes["/api/v2/system/debug/export"] = DebugExportResource
        routes["/api/v2/system/version"] = VersionResource
    except ImportError:
        pass

    try:
        from summit_rcm.rest_api.v2.login.login import LoginResource
        from summit_rcm.rest_api.v2.login.users import UsersResource
        from summit_rcm.rest_api.v2.login.users import UserResource

        routes["/api/v2/login"] = LoginResource
        routes["/api/v2/login/users"] = UsersResource
        routes["/api/v2/login/users/{username}"] = UserResource
    except ImportError:
        pass

    generate_api_spec(routes)


def run_setup(CYTHON):
    if os.environ.get("DOCS_GENERATION", "False") == "True":
        generate_docs()

    if CYTHON:
        cmdclass, ext_modules = get_cython_options()
    else:
        cmdclass, ext_modules = {}, [openssl_extension_module]

    setup(
        name="summit-rcm",
        cmdclass=cmdclass,
        version="1.0",
        packages=packages,
        scripts=["summit-rcm"],
        ext_modules=ext_modules,
    )


def status_msgs(*msgs):
    print("*" * 75, *msgs, "*" * 75, sep="\n")


if not CYTHON:
    run_setup(False)
elif os.environ.get("SUMMIT_RCM_DISABLE_CYTHON"):
    run_setup(False)
    status_msgs(
        "SUMMIT_RCM_DISABLE_CYTHON is set, skipping cython compilation.",
        "Pure-Python build succeeded.",
    )
else:
    try:
        run_setup(True)
    except BuildFailed as exc:
        status_msgs(
            exc.__cause__,
            "Cython compilation could not be completed, speedups are not enabled.",
            "Failure information, if any, is above.",
            "Retrying the build without the C extension now.",
        )

        run_setup(False)

        status_msgs(
            "Cython compilation could not be completed, speedups are not enabled.",
            "Pure-Python build succeeded.",
        )
