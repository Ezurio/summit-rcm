#!/usr/bin/python
#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2025 Ezurio LLC.
#
"""
Generate the OpenAPI spec for the Summit RCM REST API
"""


def generate_docs():
    """Generate the OpenAPI spec for the Summit RCM REST API"""
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
            NetworkInterfaceStationDumpResource,
            NetworkInterfaceAvailableApChannelsResource,
            NetworkInterfaceDhcpLeasesResource,
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
        routes["/api/v2/network/interfaces/{name}/stationDump"] = (
            NetworkInterfaceStationDumpResource
        )
        routes["/api/v2/network/interfaces/{name}/availableApChannels"] = (
            NetworkInterfaceAvailableApChannelsResource
        )
        routes["/api/v2/network/interfaces/{name}/dhcpLeases"] = (
            NetworkInterfaceDhcpLeasesResource
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
            NetworkInterfaceStationDump,
            NetworkInterfaceAvailableApChannels,
            NetworkInterfaceDhcpLeases,
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
        routes["/networkInterfaceStationDump"] = NetworkInterfaceStationDump
        routes["/networkInterfaceAvailableApChannels"] = (
            NetworkInterfaceAvailableApChannels
        )
        routes["/networkInterfaceDhcpLeases"] = NetworkInterfaceDhcpLeases
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


if __name__ == "__main__":
    generate_docs()
