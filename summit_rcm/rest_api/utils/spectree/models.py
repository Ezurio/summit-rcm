#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""Module to hold SpecTree Models"""

from typing import Any, Dict, List, Optional
from pydantic import (
    BaseModel as PydanticBaseModel,
    RootModel as PydanticRootModel,
    Field,
)
from spectree import BaseFile

from summit_rcm.definition import (
    DriverLogLevelEnum,
    JournalctlLogTypesEnum,
    PowerStateEnum,
    SupplicantLogLevelEnum,
)
from summit_rcm.services.firmware_update_service import SummitRCMUpdateStatus
from summit_rcm.services.network_manager_service import (
    NM_SETTING_8021X_DEFAULTS,
    NM_SETTING_CONNECTION_DEFAULTS,
    NM_SETTING_IP4CONFIG_DEFAULTS,
    NM_SETTING_IP6CONFIG_DEFAULTS,
    NM_SETTING_IPCONFIG_DEFAULTS,
    NM_SETTING_WIRED_DEFAULTS,
    NM_SETTING_WIRELESS_DEFAULTS,
    NM_SETTING_WIRELESS_SECURITY_DEFAULTS,
    NM_SETTING_GSM_DEFAULTS,
)


class RootModel(PydanticRootModel):
    class Config:
        arbitrary_types_allowed = True


class BaseModel(PydanticBaseModel):
    class Config:
        arbitrary_types_allowed = True


class BadRequestErrorResponseModel(RootModel):
    """Model for a 400 (Bad Request) error response"""

    root: None


class UnauthorizedErrorResponseModel(RootModel):
    """Model for a 401 (Unauthorized) error response"""

    root: None


class ForbiddenErrorResponseModel(RootModel):
    """Model for a 403 (Forbidden) error response"""

    root: None


class NotFoundErrorResponseModel(RootModel):
    """Model for a 404 (Not Found) error response"""

    root: None


class ConflictErrorResponseModel(RootModel):
    """Model for a 409 (Conflict) error response"""

    root: None


class LengthRequiredErrorResponseModel(RootModel):
    """Model for a 411 (Length Required) error response"""

    root: None


class UnsupportedMediaTypeErrorResponseModel(RootModel):
    """Model for a 415 (Unsupported Media Type) error response"""

    root: None


class InternalServerErrorResponseModel(RootModel):
    """Model for a 500 (Internal Server Error) error response"""

    root: None


class DefaultResponseModelLegacy(BaseModel):
    """Model for the default response (legacy)"""

    SDCERR: int
    InfoMsg: str = Field(default="")


class UserResponseModel(BaseModel):
    """Model for a user"""

    username: str
    permissions: str


class UsersResponseModel(RootModel):
    """Model for all users"""

    root: List[UserResponseModel]


class NewUserRequestModel(BaseModel):
    """Model for a new user"""

    username: str
    password: str
    permissions: str


class UpdateUserRequestModel(BaseModel):
    """Model for updating a user"""

    newPassword: str
    currentPassword: str
    permissions: str


class UpdateUserRequestModelLegacy(BaseModel):
    """Model for a request to update a user (legacy)"""

    new_password: str
    current_password: str
    permissions: str


class UpdateUserResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for response to a request to update a user (legacy)"""

    REDIRECT: int


class UsernameQuery(BaseModel):
    """Model for a username query"""

    username: str


class ConnectionUuidQuery(BaseModel):
    """Model for a connection UUID query"""

    uuid: str


class ConnectionProfileInfoUuidQuery(ConnectionUuidQuery):
    """Model for a query to retrieve connection profile info by UUID"""

    extended: Optional[str] = Field(default="true")


class LoginRequestModel(BaseModel):
    """Login credentials"""

    username: str = Field(default="root")
    password: str = Field(default="summit")


class LoginResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for response to a request to login (legacy)"""

    REDIRECT: int
    PERMISSION: str


class GetUsersResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for the response to a request to get all user info (legacy)"""

    REDIRECT: int
    Default_user: str
    Users: dict
    Count: int


class SystemConfigExportRequestModel(BaseModel):
    """Model for a request to export the system config"""

    password: str


class SystemConfigImportRequestFormModel(BaseModel):
    """Model for a request to import a system config"""

    archive: BaseFile
    password: str


class GetDateTimeResponseModel(BaseModel):
    """Model for the response to a request to get the current date/time info"""

    zones: List[str]
    zone: str
    datetime: str


class GetDateTimeResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for the response to a request to get the current date/time info (legacy)"""

    zones: List[str]
    zone: str
    method: str
    time: str


class SetDateTimeRequestModel(BaseModel):
    """Model for a request to set the current date/time info"""

    zone: Optional[str] = None
    datetime: Optional[str] = None


class SetDateTimeRequestModelLegacy(BaseModel):
    """Model for a request to set the current date/time info (legacy)"""

    zone: Optional[str] = None
    datetime: Optional[str] = None
    method: Optional[str] = None


class SetDateTimeResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for the response to a request to set the current date/time info (legacy)"""

    time: Optional[str] = None


class FactoryResetModel(BaseModel):
    """Model for a factory reset request/response"""

    initiateFactoryReset: str
    autoReboot: str


class FIPSModel(BaseModel):
    """Model for a FIPS request/response"""

    state: str


class FIPSSetRequestModelLegacy(BaseModel):
    """Model for a request to set FIPS mode (legacy)"""

    fips: str


class FIPSInfoResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for a response to a request for FIPS info (legacy)"""

    status: str


class LogsExportRequestModel(BaseModel):
    """Model for log export request"""

    password: str


class LogsDataRequestQuery(BaseModel):
    """Model for log data request query"""

    priority: Optional[int] = Field(
        ge=0,
        le=7,
        default=7,
    )
    days: Optional[int] = Field(ge=0, default=1)
    type: Optional[JournalctlLogTypesEnum] = Field(default=JournalctlLogTypesEnum.ALL)


class LogData(BaseModel):
    """A single journal log entry"""

    time: str
    priority: str
    identifier: str
    message: str


class LogsDataResponseModel(RootModel):
    """Model for log data response"""

    root: List[LogData]


class LogsDataResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for log data response (legacy)"""

    count: Optional[int] = None
    log: Optional[List[LogData]] = None


class LogVerbosity(BaseModel):
    """Model for a log verbosity request/response"""

    suppDebugLevel: SupplicantLogLevelEnum
    driverDebugLevel: DriverLogLevelEnum


class LogVerbosityResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for a log verbosity response (legacy)"""

    suppDebugLevel: Optional[str] = None
    driverDebugLevel: Optional[str] = None
    Errormsg: Optional[str] = None


class WebserverLogLevel(BaseModel):
    """Model for a webserver log level request/response"""

    webserverLogLevel: str


class WebserverLogLevelResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for a webserver log level response (legacy)"""

    webserverLogLevel: str


class ChronyNTPSource(BaseModel):
    """Model for a chrony NTP source"""

    address: str
    type: str


class ChronyNTPSources(RootModel):
    """Model for a Chrony NTP sources request/response"""

    root: List[ChronyNTPSource]


class PowerState(BaseModel):
    """Model for power state request/response"""

    state: PowerStateEnum


class FirmwareUpdateStatus(BaseModel):
    """Model for firmware update status request/response"""

    status: Optional[SummitRCMUpdateStatus] = None
    url: Optional[str] = None
    image: Optional[str] = None


class FirmwareUpdateModelLegacy(BaseModel):
    """Model for firmware update status request/response (legacy)"""

    url: Optional[str] = None
    image: Optional[str] = Field(default="main")


class VersionInfo(BaseModel):
    """Model for version info response"""

    nmVersion: str
    summitRcm: str
    build: str
    supplicant: str
    radioStack: str
    driver: str
    kernelVermagic: str
    bluez: str
    uBoot: str
    currentSide: str
    nextSide: str
    baseHwPartNumber: str


class VersionInfoLegacy(DefaultResponseModelLegacy):
    """Model for version info response (legacy)"""

    nm_version: str
    summit_rcm: str
    build: str
    supplicant: str
    radio_stack: str
    driver: str
    kernel_vermagic: str
    bluez: str
    uboot: str = Field(alias="u-boot")
    current_side: str
    next_side: str
    base_hw_part_number: str


class AccessPoint(BaseModel):
    """Model for an access point"""

    ssid: Optional[str] = None
    hwAddress: Optional[str] = None
    strength: Optional[int] = None
    maxBitrate: Optional[int] = None
    frequency: Optional[int] = None
    channel: Optional[int] = None
    flags: Optional[int] = None
    wpaFlags: Optional[int] = None
    rsnFlags: Optional[int] = None
    lastSeen: Optional[int] = None
    security: Optional[str] = None
    keymgmt: Optional[str] = None


class AccessPointLegacy(BaseModel):
    """Model for an access point (legacy)"""

    SSID: Optional[str] = None
    HwAddress: Optional[str] = None
    Strength: Optional[int] = None
    MaxBitrate: Optional[int] = None
    Frequency: Optional[int] = None
    Channel: Optional[int] = None
    Flags: Optional[int] = None
    WpaFlags: Optional[int] = None
    RsnFlags: Optional[int] = None
    LastSeen: Optional[int] = None
    Security: Optional[str] = None
    Keymgmt: Optional[str] = None


class ActiveAccessPoint(AccessPoint):
    """Model for an active access point"""

    signal: Optional[float] = None


class ActiveAccessPointLegacy(BaseModel):
    """Model for an active access point (legacy)"""

    Ssid: Optional[str] = None
    HwAddress: Optional[str] = None
    Maxbitrate: Optional[int] = None
    Flags: Optional[int] = None
    Wpaflags: Optional[int] = None
    Rsnflags: Optional[int] = None
    Strength: Optional[int] = None
    Frequency: Optional[int] = None
    Channel: Optional[int] = None
    Signal: Optional[float] = None


class AccessPoints(RootModel):
    """Model for an access points response"""

    root: List[AccessPoint]


class AccessPointsResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for an access points response (legacy)"""

    count: int
    accesspoints: List[AccessPointLegacy]
    secondsSinceLastScan: int


class AccessPointScanRequestReponseModel(BaseModel):
    """Model for the response to a request for an access point scan"""

    scanRequested: bool


class AccessPointSecondsSinceLastScanResponseModel(BaseModel):
    """Model for the seconds since the last access point scan"""

    secondsSinceLastScan: int


class CertificateFiles(RootModel):
    """Model for certificate files response"""

    root: List[str]


class CertificateInfoRequest(BaseModel):
    """Model for a certificate info request"""

    password: Optional[str] = None


class CertificateInfoExtension(BaseModel):
    """Model for a certificate info extension"""

    name: str
    value: str


class CertificateInfoResponse(BaseModel):
    """Model for a certificate info response"""

    version: int
    serial_number: str
    subject: str
    issuer: str
    not_before: str
    not_after: str
    extensions: List[CertificateInfoExtension]


class CertificateInfoRequestQueryLegacy(BaseModel):
    """Model for a certificate info request query (legacy)"""

    name: Optional[str] = None
    password: Optional[str] = None


class CertificateInfoResponseLegacy(DefaultResponseModelLegacy):
    """Model for a certificate info response (legacy)"""

    cert_info: Optional[CertificateInfoResponse] = None
    files: Optional[List[str]] = None
    count: Optional[int] = None


class CertificateUploadRequestFormModel(BaseModel):
    """Model for a request to upload a certificate"""

    file: BaseFile


class FileUploadRequestModelLegacy(BaseModel):
    """Model for a request to upload a file (legacy)"""

    type: str
    password: Optional[str] = None
    file: BaseFile


class FileDownloadQueryModelLegacy(BaseModel):
    """Model for a file download query (legacy)"""

    type: str
    password: Optional[str] = None


class FileDeleteQueryModelLegacy(BaseModel):
    """Model for a file delete query (legacy)"""

    type: str
    file: str


class FileInfoRequestQueryModelLegacy(BaseModel):
    """Model for a file info request query (legacy)"""

    type: str
    password: Optional[str] = None


class FileInfoResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for a file info response (legacy)"""

    files: Optional[List[str]] = None
    count: Optional[int] = None


class ConnectionProfileInfo(BaseModel):
    """Model for info about a connection profile"""

    id: str
    uuid: str
    type: str
    activated: bool


class ConnectionProfileInfoLegacy(BaseModel):
    """Model for info about a connection profile (legacy)"""

    id: str
    type: str
    activated: int


class ActivateConnectionRequestModelLegacy(BaseModel):
    """Model for a request to activate/deactivate a connection (legacy)"""

    uuid: str
    activate: int


class ConnectionSettingsConnectionModel(BaseModel):
    """Model for the 'connection' setting of a NetworkManager Connection"""

    auth_retries: Optional[int] = Field(
        alias="auth-retries",
        default=NM_SETTING_CONNECTION_DEFAULTS["auth-retries"],
        description=(
            "The number of retries for the authentication. Zero means to try indefinitely; "
            "-1 means to use a global default. If the global default is not set, the "
            "authentication retries for 3 times before failing the connection. Currently, this "
            "only applies to 802-1x authentication."
        ),
    )
    autoconnect: Optional[bool] = Field(
        default=NM_SETTING_CONNECTION_DEFAULTS["autoconnect"],
        description=(
            "Whether or not the connection should be automatically connected by "
            "NetworkManager when the resources for the connection are available. TRUE to "
            "automatically activate the connection, FALSE to require manual intervention "
            "to activate the connection. Autoconnect happens when the circumstances are "
            "suitable. That means for example that the device is currently managed and not "
            "active. Autoconnect thus never replaces or competes with an already active "
            "profile. Note that autoconnect is not implemented for VPN profiles. See "
            "\"secondaries\" as an alternative to automatically connect VPN profiles. If "
            "multiple profiles are ready to autoconnect on the same device, the one with "
            "the better \"connection.autoconnect-priority\" is chosen. If the priorities "
            "are equal, then the most recently connected profile is activated. If the "
            "profiles were not connected earlier or their \"connection.timestamp\" is "
            "identical, the choice is undefined. Depending on \"connection.multi-connect\", "
            "a profile can (auto)connect only once at a time or multiple times."
        ),
    )
    autoconnect_ports: Optional[int] = Field(
        alias="autoconnect-ports",
        default=NM_SETTING_CONNECTION_DEFAULTS["autoconnect-ports"],
        description=(
            "Whether or not ports of this connection should be automatically brought up "
            "when NetworkManager activates this connection. This only has a real effect "
            "for controller connections. The properties 'autoconnect', 'autoconnect-priority' "
            "and 'autoconnect-retries' are unrelated to this setting. The permitted values are: "
            "0: leave port connections untouched, 1: activate all the port connections with this "
            "connection, -1: default. If -1 (default) is set, global connection.autoconnect-ports "
            "is read to determine the real value. If it is default as well, this fallbacks to 0."
        ),
    )
    autoconnect_priority: Optional[int] = Field(
        alias="autoconnect-priority",
        default=NM_SETTING_CONNECTION_DEFAULTS["autoconnect-priority"],
        description=(
            "The autoconnect priority in range -999 to 999. If the connection is set to "
            "autoconnect, connections with higher priority will be preferred. The higher "
            "number means higher priority. Defaults to 0. Note that this property only "
            "matters if there are more than one candidate profile to select for autoconnect. "
            "In case of equal priority, the profile used most recently is chosen."
        ),
    )
    autoconnect_retries: Optional[int] = Field(
        alias="autoconnect-retries",
        default=NM_SETTING_CONNECTION_DEFAULTS["autoconnect-retries"],
        description=(
            "The number of times a connection should be tried when autoactivating before giving "
            "up. Zero means forever, -1 means the global default (4 times if not overridden). "
            "Setting this to 1 means to try activation only once before blocking autoconnect. Note "
            "that after a timeout, NetworkManager will try to autoconnect again."
        ),
    )
    autoconnect_slaves: Optional[int] = Field(
        alias="autoconnect-slaves",
        default=NM_SETTING_CONNECTION_DEFAULTS["autoconnect-slaves"],
        description=(
            "Whether or not ports of this connection should be automatically brought up "
            "when NetworkManager activates this connection. This only has a real effect "
            "for controller connections. The properties \"autoconnect\", \"autoconnect-priority\" "
            "and \"autoconnect-retries\" are unrelated to this setting. The permitted values are: "
            "0: leave port connections untouched, 1: activate all the port connections with this "
            "connection, -1: default. If -1 (default) is set, global connection.autoconnect-slaves "
            "is read to determine the real value. If it is default as well, this fallbacks to 0. "
            "Deprecated 1.46. Use \"autoconnect-ports\" instead, this is just an alias."
        ),
        deprecated=(
            "Deprecated 1.46. Use \"autoconnect-ports\" instead, this is just an alias."
        ),
    )
    controller: Optional[str] = Field(
        default=NM_SETTING_CONNECTION_DEFAULTS["controller"],
        description="Interface name of the controller device or UUID of the controller connection."
    )
    dns_over_tls: Optional[int] = Field(
        alias="dns-over-tls",
        default=NM_SETTING_CONNECTION_DEFAULTS["dns-over-tls"],
        description=(
            "Whether DNSOverTls (dns-over-tls) is enabled for the connection. DNSOverTls is a "
            "technology which uses TLS to encrypt dns traffic. The permitted values are: "
            "\"yes\" (2) use DNSOverTls and disabled fallback, \"opportunistic\" (1) use "
            "DNSOverTls but allow fallback to unencrypted resolution, \"no\" (0) don't ever use "
            "DNSOverTls. If unspecified \"default\" depends on the plugin used. Systemd-resolved "
            "uses global setting. This feature requires a plugin which supports DNSOverTls. "
            "Otherwise, the setting has no effect. One such plugin is dns-systemd-resolved."
        ),
    )
    down_on_poweroff: Optional[int] = Field(
        alias="down-on-poweroff",
        default=NM_SETTING_CONNECTION_DEFAULTS["down-on-poweroff"],
        description=(
            "Whether the connection will be brought down before the system is powered off. "
            "The default value is -1 (default). When the default value is specified, then the "
            "global value from NetworkManager configuration is looked up, if not set, it is "
            "considered as 0 (no)."
        ),
    )
    gateway_ping_timeout: Optional[int] = Field(
        alias="gateway-ping-timeout",
        default=NM_SETTING_CONNECTION_DEFAULTS["gateway-ping-timeout"],
        description=(
            "If greater than zero, delay success of IP addressing until either the timeout "
            "is reached, or an IP gateway replies to a ping."
        ),
    )
    id: Optional[str] = Field(
        default=NM_SETTING_CONNECTION_DEFAULTS["id"],
        description=(
            "A human readable unique identifier for the connection, "
            "like \"Work Wi-Fi\" or \"T-Mobile 3G\"."
        ),
    )
    interface_name: Optional[str] = Field(
        alias="interface-name",
        default=NM_SETTING_CONNECTION_DEFAULTS["interface-name"],
        description=(
            "The name of the network interface this connection is bound to. If not set, "
            "then the connection can be attached to any interface of the appropriate type "
            "(subject to restrictions imposed by other settings). For software devices this "
            "specifies the name of the created device. For connection types where interface "
            "names cannot easily be made persistent (e.g. mobile broadband or USB Ethernet), "
            "this property should not be used. Setting this property restricts the interfaces "
            "a connection can be used with, and if interface names change or are reordered the "
            "connection may be applied to the wrong interface."
        ),
    )
    ip_ping_addresses: Optional[List[str]] = Field(
        alias="ip-ping-addresses",
        default=NM_SETTING_CONNECTION_DEFAULTS["ip-ping-addresses"],
        description=(
            "The property specifies a list of target IP addresses for pinging. When multiple "
            "targets are set, NetworkManager will start multiple ping processes in parallel. "
            "This property can only be set if connection.ip-ping-timeout is set. The "
            "ip-ping-timeout is used to delay the success of IP addressing until either the "
            "specified timeout (in seconds) is reached, or a target IP address replies to a ping. "
            "Configuring \"ip-ping-addresses\" may delay reaching the systemd's "
            "network-online.target due to waiting for the ping operations to complete or timeout."
        ),
    )
    ip_ping_addresses_require_all: Optional[int] = Field(
        alias="ip-ping-addresses-require-all",
        default=NM_SETTING_CONNECTION_DEFAULTS["ip-ping-addresses-require-all"],
        description=(
            "The property determines whether it is sufficient for any ping check to succeed "
            "among \"ip-ping-addresses\", or if all ping checks must succeed for "
            "\"ip-ping-addresses\"."
        ),
    )
    ip_ping_timeout: Optional[int] = Field(
        alias="ip-ping-timeout",
        default=NM_SETTING_CONNECTION_DEFAULTS["ip-ping-timeout"],
        description=(
            "If greater than zero, delay success of IP addressing until either the specified "
            "timeout (in seconds) is reached, or a target IP address replies to a ping. The "
            "property specifies the timeout for the \"ip-ping-addresses\". This property is "
            "incompatible with \"gateway-ping-timeout\", you cannot set these two properties at "
            "the same time."
        ),
    )
    lldp: Optional[int] = Field(
        default=NM_SETTING_CONNECTION_DEFAULTS["lldp"],
        description="Whether LLDP is enabled for the connection.",
    )
    llmnr: Optional[int] = Field(
        default=NM_SETTING_CONNECTION_DEFAULTS["llmnr"],
        description=(
            "Whether Link-Local Multicast Name Resolution (LLMNR) is enabled for the connection. "
            "LLMNR is a protocol based on the Domain Name System (DNS) packet format that allows "
            "both IPv4 and IPv6 hosts to perform name resolution for hosts on the same local link. "
            "The permitted values are: \"yes\" (2) register hostname and resolving for the "
            "connection, \"no\" (0) disable LLMNR for the interface, \"resolve\" (1) do not "
            "register hostname but allow resolving of LLMNR host names. If unspecified, "
            "\"default\" ultimately depends on the DNS plugin (which for systemd-resolved "
            "currently means \"yes\"). This feature requires a plugin which supports LLMNR. "
            "Otherwise, the setting has no effect. One such plugin is dns-systemd-resolved."
        ),
    )
    master: Optional[str] = Field(
        default=NM_SETTING_CONNECTION_DEFAULTS["master"],
        description=(
            "Interface name of the controller device or UUID of the controller connection. "
            "Deprecated 1.46. Use \"controller\" instead, this is just an alias."
        ),
        deprecated="Deprecated 1.46. Use \"controller\" instead, this is just an alias.",
    )
    mdns: Optional[int] = Field(
        default=NM_SETTING_CONNECTION_DEFAULTS["mdns"],
        description=(
            "Whether mDNS is enabled for the connection. The permitted values are: \"yes\" (2) "
            "register hostname and resolving for the connection, \"no\" (0) disable mDNS for the "
            "interface, \"resolve\" (1) do not register hostname but allow resolving of mDNS host "
            "names and \"default\" (-1) to allow lookup of a global default in "
            "NetworkManager.conf. If unspecified, \"default\" ultimately depends on the DNS "
            "plugin. This feature requires a plugin which supports mDNS. Otherwise, the setting "
            "has no effect. Currently the only supported DNS plugin is systemd-resolved. For "
            "systemd-resolved, the default is configurable via MulticastDNS= setting in "
            "resolved.conf."
        ),
    )
    metered: Optional[int] = Field(
        default=NM_SETTING_CONNECTION_DEFAULTS["metered"],
        description=(
            "Whether the connection is metered. When updating this property on a currently "
            "activated connection, the change takes effect immediately."
        ),
    )
    mptcp_flags: Optional[int] = Field(
        alias="mptcp-flags",
        default=NM_SETTING_CONNECTION_DEFAULTS["mptcp-flags"],
        description=(
            "Whether to configure MPTCP endpoints and the address flags. If MPTCP is enabled in "
            "NetworkManager, it will configure the addresses of the interface as MPTCP endpoints. "
            "Note that IPv4 loopback addresses (127.0.0.0/8), IPv4 link local addresses "
            "(169.254.0.0/16), the IPv6 loopback address (::1), IPv6 link local addresses "
            "(fe80::/10), IPv6 unique local addresses (ULA, fc00::/7) and IPv6 privacy extension "
            "addresses (rfc3041, ipv6.ip6-privacy) will be excluded from being configured as "
            "endpoints. If \"disabled\" (0x1), MPTCP handling for the interface is disabled and no "
            "endpoints are registered. The \"enabled\" (0x2) flag means that MPTCP handling is "
            "enabled. This flag can also be implied from the presence of other flags. Even when "
            "enabled, MPTCP handling will by default still be disabled unless "
            "\"/proc/sys/net/mptcp/enabled\" sysctl is on. NetworkManager does not change the "
            "sysctl and this is up to the administrator or distribution. To configure endpoints "
            "even if the sysctl is disabled, \"also-without-sysctl\" (0x4) flag can be used. In "
            "that case, NetworkManager doesn't look at the sysctl and configures endpoints "
            "regardless. Even when enabled, NetworkManager will only configure MPTCP endpoints for "
            "a certain address family, if there is a unicast default route (0.0.0.0/0 or ::/0) in "
            "the main routing table. The flag \"also-without-default-route\" (0x8) can override "
            "that. When MPTCP handling is enabled then endpoints are configured with the specified "
            "address flags \"signal\" (0x10), \"subflow\" (0x20), \"backup\" (0x40), \"fullmesh\" "
            "(0x80). See ip-mptcp(8) manual for additional information about the flags. If the "
            "flags are zero (0x0), the global connection default from NetworkManager.conf is "
            "honored. If still unspecified, the fallback is \"enabled,subflow\". Note that this "
            "means that MPTCP is by default done depending on the \"/proc/sys/net/mptcp/enabled\" "
            "sysctl. NetworkManager does not change the MPTCP limits nor enable MPTCP via "
            "\"/proc/sys/net/mptcp/enabled\". That is a host configuration which the admin can "
            "change via sysctl and ip-mptcp. Strict reverse path filtering (rp_filter) breaks many "
            "MPTCP use cases, so when MPTCP handling for IPv4 addresses on the interface is "
            "enabled, NetworkManager would loosen the strict reverse path filtering (1) to the "
            "loose setting (2)."
        ),
    )
    mud_url: Optional[str] = Field(
        alias="mud-url",
        default=NM_SETTING_CONNECTION_DEFAULTS["mud-url"],
        description=(
            "If configured, set to a Manufacturer Usage Description (MUD) URL that points to "
            "manufacturer-recommended network policies for IoT devices. It is transmitted as a "
            "DHCPv4 or DHCPv6 option. The value must be a valid URL starting with \"https://\". "
            "The special value \"none\" is allowed to indicate that no MUD URL is used. If the "
            "per-profile value is unspecified (the default), a global connection default gets "
            "consulted. If still unspecified, the ultimate default is \"none\"."
        ),
    )
    multi_connect: Optional[int] = Field(
        alias="multi-connect",
        default=NM_SETTING_CONNECTION_DEFAULTS["multi-connect"],
        description=(
            "Specifies whether the profile can be active multiple times at a particular moment. "
            "The value is of type NMConnectionMultiConnect."
        ),
    )
    permissions: Optional[List[str]] = Field(
        default=NM_SETTING_CONNECTION_DEFAULTS["permissions"],
        description=(
            "An array of strings defining what access a given user has to this connection. "
            "If this is NULL or empty, all users are allowed to access this connection; "
            "otherwise users are allowed if and only if they are in this list. When this is "
            "not empty, the connection can be active only when one of the specified users is "
            "logged into an active session. Each entry is of the form \"[type]:[id]:[reserved]\"; "
            "for example, \"user:dcbw:blah\". At this time only the \"user\" [type] is allowed. "
            "Any other values are ignored and reserved for future use. [id] is the username "
            "that this permission refers to, which may not contain the \":\" character. Any "
            "[reserved] information present must be ignored and is reserved for future use. "
            "All of [type], [id], and [reserved] must be valid UTF-8."
        ),
    )
    port_type: Optional[str] = Field(
        alias="port-type",
        default=NM_SETTING_CONNECTION_DEFAULTS["port-type"],
        description=(
            "Setting name of the device type of this port's controller connection "
            "(e.g., \"bond\"), or NULL if this connection is not a port."
        ),
    )
    read_only: Optional[bool] = Field(
        alias="read-only",
        default=NM_SETTING_CONNECTION_DEFAULTS["read-only"],
        description=(
            "This property is deprecated since version 1.44."
            "This property is deprecated and has no meaning. "
        ),
        deprecated=(
            "This property is deprecated since version 1.44. "
            "This property is deprecated and has no meaning."
        ),
    )
    secondaries: Optional[List[str]] = Field(
        default=NM_SETTING_CONNECTION_DEFAULTS["secondaries"],
        description=(
            "List of connection UUIDs that should be activated when the base connection "
            "itself is activated. Currently, only VPN connections are supported."
        ),
    )
    slave_type: Optional[str] = Field(
        alias="slave-type",
        default=NM_SETTING_CONNECTION_DEFAULTS["slave-type"],
        description=(
            "Setting name of the device type of this port's controller connection (eg, "
            "\"bond\"), or NULL if this connection is not a port. Deprecated 1.46. Use "
            "\"port-type\" instead, this is just an alias."
        ),
        deprecated="Deprecated 1.46. Use \"port-type\" instead, this is just an alias.",
    )
    stable_id: Optional[str] = Field(
        alias="stable-id",
        default=NM_SETTING_CONNECTION_DEFAULTS["stable-id"],
        description=(
            "This represents the identity of the connection used for various purposes. "
            "It allows configuring multiple profiles to share the identity. Also, the stable-id "
            "can contain placeholders that are substituted dynamically and deterministically "
            "depending on the context. The stable-id is used for generating IPv6 stable private "
            "addresses with ipv6.addr-gen-mode=stable-privacy. It is also used to seed the "
            "generated cloned MAC address for ethernet.cloned-mac-address=stable and "
            "wifi.cloned-mac-address=stable. It is also used to derive the DHCP client identifier "
            "with ipv4.dhcp-client-id=stable, the DHCPv6 DUID with "
            "ipv6.dhcp-duid=stable-[llt,ll,uuid] and the DHCP IAID with ipv4.iaid=stable and "
            "ipv6.iaid=stable. Note that depending on the context where it is used, other "
            "parameters are also seeded into the generation algorithm. For example, a per-host key "
            "is commonly also included, so that different systems end up generating different IDs. "
            "Or with ipv6.addr-gen-mode=stable-privacy, also the device's name is included, so "
            "that different interfaces yield different addresses. The per-host key is the identity "
            "of your machine and stored in /var/lib/NetworkManager/secret_key. See "
            "NetworkManager(8) manual about the secret-key and the host identity. The '$' "
            "character is treated specially to perform dynamic substitutions at activation time. "
            "Currently, supported are '\"${CONNECTION}\", \"${DEVICE}\", \"${MAC}\", "
            "\"${NETWORK_SSID}\", \"${BOOT}\", \"${RANDOM}\". These effectively create unique IDs "
            "per-connection, per-device, per-SSID, per-boot, or every time. The \"${CONNECTION}\" "
            "uses the profile's connection.uuid, the \"${DEVICE}\" uses the interface name of the "
            "device and \"${MAC}\" the permanent MAC address of the device. \"${NETWORK_SSID}\" "
            "uses the SSID for Wi-Fi networks and falls back to \"${CONNECTION}\" on other "
            "networks. Any unrecognized patterns following '$' are treated verbatim, however, are "
            "reserved for future use. You are thus advised to avoid '$' or escape it as \"$$\". "
            "For example, set it to \"${CONNECTION}-${BOOT}-${DEVICE}\" to create a unique id for "
            "this connection that changes with every reboot and differs depending on the interface "
            "where the profile activates. If the value is unset, a global connection default is "
            "consulted. If the value is still unset, the default is \"default${CONNECTION}\" to "
            "generate an ID unique per connection profile."
        ),
    )
    timestamp: Optional[int] = Field(
        default=NM_SETTING_CONNECTION_DEFAULTS["timestamp"],
        description=(
            "The time, in seconds since the Unix Epoch, that the connection was last "
            "_successfully_ fully activated. NetworkManager updates the connection timestamp "
            "periodically when the connection is active to ensure that an active connection has "
            "the latest timestamp. The property is only meant for reading (changes to this "
            "property will not be preserved)."
        ),
    )
    type: Optional[str] = Field(
        default=NM_SETTING_CONNECTION_DEFAULTS["type"],
        description=(
            "Base type of the connection. For hardware-dependent connections, should contain "
            "the setting name of the hardware-type specific setting (i.e., \"802-3-ethernet\" or "
            "\"802-11-wireless\" or \"bluetooth\", etc), and for non-hardware dependent "
            "connections like VPN or otherwise, should contain the setting name of that setting "
            "type (i.e., \"vpn\" or \"bridge\", etc)."
        ),
    )
    uuid: Optional[str] = Field(
        default=NM_SETTING_CONNECTION_DEFAULTS["uuid"],
        description=(
            "A universally unique identifier for the connection, for example generated with "
            "libuuid. It should be assigned when the connection is created, and never changed as "
            "long as the connection still applies to the same network. For example, it should not "
            "be changed when the \"id\" property or NMSettingIP4Config changes, but might need to "
            "be re-created when the Wi-Fi SSID, mobile broadband network provider, or \"type\" "
            "property changes. The UUID must be in the format "
            "\"2815492f-7e56-435e-b2e9-246bd7cdc664\" (ie, contains only hexadecimal characters "
            "and \"-\")."
        ),
    )
    wait_activation_delay: Optional[int] = Field(
        alias="wait-activation-delay",
        default=NM_SETTING_CONNECTION_DEFAULTS["wait-activation-delay"],
        description=(
            "Time in milliseconds to wait for connection to be considered activated. The "
            "wait will start after the pre-up dispatcher event. The value 0 means no wait time. "
            "The default value is -1, which currently has the same meaning as no wait time."
        ),
    )
    wait_device_timeout: Optional[int] = Field(
        alias="wait-device-timeout",
        default=NM_SETTING_CONNECTION_DEFAULTS["wait-device-timeout"],
        description=(
            "Timeout in milliseconds to wait for device at startup. During boot, devices may take "
            "a while to be detected by the driver. This property will cause to delay "
            "NetworkManager-wait-online.service and nm-online to give the device a chance to "
            "appear. This works by waiting for the given timeout until a compatible device for the "
            "profile is available and managed. The value 0 means no wait time. The default value "
            "is -1, which currently has the same meaning as no wait time."
        ),
    )
    zone: Optional[str] = Field(
        default=NM_SETTING_CONNECTION_DEFAULTS["zone"],
        description=(
            "The trust level of a the connection. Free form case-insensitive string (for example "
            "\"Home\", \"Work\", \"Public\"). NULL or unspecified zone means the connection will "
            "be placed in the default zone as defined by the firewall. When updating this property "
            "on a currently activated connection, the change takes effect immediately."
        ),
    )


class ConnectionSettings8021xModel(BaseModel):
    """Model for the '802-1x' setting of a NetworkManager Connection"""

    altsubject_matches: Optional[List[str]] = Field(
        alias="altsubject-matches",
        default=NM_SETTING_8021X_DEFAULTS["altsubject-matches"],
        description=(
            "List of strings to be matched against the altSubjectName of the certificate "
            "presented by the authentication server. If the list is empty, no verification "
            "of the server certificate's altSubjectName is performed."
        ),
    )
    anonymous_identity: Optional[str] = Field(
        alias="anonymous-identity",
        default=NM_SETTING_8021X_DEFAULTS["anonymous-identity"],
        description=(
            "Anonymous identity string for EAP authentication methods. Used as the "
            "unencrypted identity with EAP types that support different tunneled identity "
            "like EAP-TTLS."
        ),
    )
    auth_timeout: Optional[int] = Field(
        alias="auth-timeout",
        default=NM_SETTING_8021X_DEFAULTS["auth-timeout"],
        description=(
            "A timeout for the authentication. Zero means the global default; "
            "if the global default is not set, the authentication timeout is 25 seconds."
        ),
    )
    ca_cert: Optional[str] = Field(
        alias="ca-cert",
        default=NM_SETTING_8021X_DEFAULTS["ca-cert"],
        description=(
            "Contains the CA certificate if used by the EAP method specified in the \"eap\" "
            "property. Certificate data is specified using a \"scheme\"; three are currently "
            "supported: blob, path and pkcs#11 URL. When using the blob scheme this property "
            "should be set to the certificate's DER encoded data. When using the path scheme, this "
            "property should be set to the full UTF-8 encoded path of the certificate, prefixed "
            "with the string \"file://\" and ending with a terminating NUL byte. This property can "
            "be unset even if the EAP method supports CA certificates, but this allows "
            "man-in-the-middle attacks and is NOT recommended. Note that enabling "
            "NMSetting8021x:system-ca-certs will override this setting to use the built-in path, "
            "if the built-in path is not a directory.\n"
            "NOTE: In Summit RCM, this property always uses the path scheme and is expected to be "
            "the name of a previously-uploaded certificate (e.g. \"ca-cert.pem\")."
        ),
    )
    ca_cert_password: Optional[str] = Field(
        alias="ca-cert-password",
        default=NM_SETTING_8021X_DEFAULTS["ca-cert-password"],
        description=(
            "The password used to access the CA certificate stored in \"ca-cert\" property. Only "
            "makes sense if the certificate is stored on a PKCS#11 token that requires a login."
        ),
    )
    ca_cert_password_flags: Optional[int] = Field(
        alias="ca-cert-password-flags",
        default=NM_SETTING_8021X_DEFAULTS["ca-cert-password-flags"],
        description=(
            "Flags indicating how to handle the \"ca-cert-password\" property."
        ),
    )
    ca_path: Optional[str] = Field(
        alias="ca-path",
        default=NM_SETTING_8021X_DEFAULTS["ca-path"],
        description=(
            "UTF-8 encoded path to a directory containing PEM or DER formatted certificates to be "
            "added to the verification chain in addition to the certificate specified in the "
            "\"ca-cert\" property. If NMSetting8021x:system-ca-certs is enabled and the built-in "
            "CA path is an existing directory, then this setting is ignored."
        ),
    )
    client_cert: Optional[str] = Field(
        alias="client-cert",
        default=NM_SETTING_8021X_DEFAULTS["client-cert"],
        description=(
            "Contains the client certificate if used by the EAP method specified in the \"eap\" "
            "property. Certificate data is specified using a \"scheme\"; two are currently "
            "supported: blob and path. When using the blob scheme (which is backwards compatible "
            "with NM 0.7.x) this property should be set to the certificate's DER encoded data. "
            "When using the path scheme, this property should be set to the full UTF-8 encoded "
            "path of the certificate, prefixed with the string \"file://\" and ending with a "
            "terminating NUL byte.\n"
            "NOTE: In Summit RCM, this property always uses the path scheme and is expected to be "
            "the name of a previously-uploaded certificate (e.g. \"client-cert.pem\")."
        ),
    )
    client_cert_password: Optional[str] = Field(
        alias="client-cert-password",
        default=NM_SETTING_8021X_DEFAULTS["client-cert-password"],
        description=(
            "The password used to access the client certificate stored in \"client-cert\" "
            "property. Only makes sense if the certificate is stored on a PKCS#11 token that "
            "requires a login."
        ),
    )
    client_cert_password_flags: Optional[int] = Field(
        alias="client-cert-password-flags",
        default=NM_SETTING_8021X_DEFAULTS["client-cert-password-flags"],
        description=(
            "Flags indicating how to handle the \"client-cert-password\" property."
        ),
    )
    domain_match: Optional[str] = Field(
        alias="domain-match",
        default=NM_SETTING_8021X_DEFAULTS["domain-match"],
        description=(
            "Constraint for server domain name. If set, this list of FQDNs is used as a match "
            "requirement for dNSName element(s) of the certificate presented by the authentication "
            "server. If a matching dNSName is found, this constraint is met. If no dNSName values "
            "are present, this constraint is matched against SubjectName CN using the same "
            "comparison. Multiple valid FQDNs can be passed as a \";\" delimited list."
        ),
    )
    domain_suffix_match: Optional[str] = Field(
        alias="domain-suffix-match",
        default=NM_SETTING_8021X_DEFAULTS["domain-suffix-match"],
        description=(
            "Constraint for server domain name. If set, this FQDN is used as a suffix match "
            "requirement for dNSName element(s) of the certificate presented by the authentication "
            "server. If a matching dNSName is found, this constraint is met. If no dNSName values "
            "are present, this constraint is matched against SubjectName CN using same suffix "
            "match comparison. Since version 1.24, multiple valid FQDNs can be passed as a \";\" "
            "delimited list."
        ),
    )
    eap: Optional[List[str]] = Field(
        default=NM_SETTING_8021X_DEFAULTS["eap"],
        description=(
            "The allowed EAP method to be used when authenticating to the network with 802.1x. "
            "Valid methods are: \"leap\", \"md5\", \"tls\", \"peap\", \"ttls\", \"pwd\", and "
            "\"fast\". Each method requires different configuration using the properties of this "
            "setting; refer to wpa_supplicant documentation for the allowed combinations."
        ),
    )
    identity: Optional[str] = Field(
        default=NM_SETTING_8021X_DEFAULTS["identity"],
        description=(
            "Identity string for EAP authentication methods. Often the user's user or login name."
        ),
    )
    openssl_ciphers: Optional[str] = Field(
        alias="openssl-ciphers",
        default=NM_SETTING_8021X_DEFAULTS["openssl-ciphers"],
        description=(
            "Define openssl_ciphers for wpa_supplicant. Openssl sometimes moves ciphers among "
            "SECLEVELs, thus compiled-in default value in wpa_supplicant (as modified by some "
            "linux distributions) sometimes prevents to connect to old servers that do not support "
            "new protocols."
        ),
    )
    optional: Optional[bool] = Field(
        default=NM_SETTING_8021X_DEFAULTS["optional"],
        description=(
            "Whether the 802.1X authentication is optional. If TRUE, the activation will continue "
            "even after a timeout or an authentication failure. Setting the property to TRUE is "
            "currently allowed only for Ethernet connections. If set to FALSE, the activation can "
            "continue only after a successful authentication."
        ),
    )
    pac_file: Optional[str] = Field(
        alias="pac-file",
        default=NM_SETTING_8021X_DEFAULTS["pac-file"],
        description=(
            "UTF-8 encoded file path containing PAC for EAP-FAST.\n"
            "In Summit RCM, this property is expected to be the name of a previously-uploaded PAC "
            "file (e.g. \"pac-file.pac\")."
        ),
    )
    password: Optional[str] = Field(
        default=NM_SETTING_8021X_DEFAULTS["password"],
        description=(
            "UTF-8 encoded password used for EAP authentication methods. If both the \"password\" "
            "property and the \"password-raw\" property are specified, \"password\" is preferred."
        ),
    )
    password_flags: Optional[int] = Field(
        alias="password-flags",
        default=NM_SETTING_8021X_DEFAULTS["password-flags"],
        description=(
            "Flags indicating how to handle the \"password\" property."
        ),
    )
    password_raw: Optional[str] = Field(
        alias="password-raw",
        default=NM_SETTING_8021X_DEFAULTS["password-raw"],
        description=(
            "Password used for EAP authentication methods, given as a byte array to allow "
            "passwords in other encodings than UTF-8 to be used. If both the \"password\" property "
            "and the \"password-raw\" property are specified, \"password\" is preferred."
        ),
    )
    password_raw_flags: Optional[int] = Field(
        alias="password-raw-flags",
        default=NM_SETTING_8021X_DEFAULTS["password-raw-flags"],
        description=(
            "Flags indicating how to handle the \"password-raw\" property."
        ),
    )
    phase1_auth_flags: Optional[int] = Field(
        alias="phase1-auth-flags",
        default=NM_SETTING_8021X_DEFAULTS["phase1-auth-flags"],
        description=(
            "Specifies authentication flags to use in \"phase 1\" outer authentication using "
            "NMSetting8021xAuthFlags options. The individual TLS versions can be explicitly "
            "disabled. TLS time checks can be also disabled. If a certain TLS disable flag is not "
            "set, it is up to the supplicant to allow or forbid it. The TLS options map to "
            "tls_disable_tlsv1_x and tls_disable_time_checks settings. See the wpa_supplicant "
            "documentation for more details."
        ),
    )
    phase1_fast_provisioning: Optional[str] = Field(
        alias="phase1-fast-provisioning",
        default=NM_SETTING_8021X_DEFAULTS["phase1-fast-provisioning"],
        description=(
            "Enables or disables in-line provisioning of EAP-FAST credentials when FAST is "
            "specified as the EAP method in the \"eap\" property. Recognized values are \"0\" "
            "(disabled), \"1\" (allow unauthenticated provisioning), \"2\" (allow authenticated "
            "provisioning), and \"3\" (allow both authenticated and unauthenticated provisioning). "
            "See the wpa_supplicant documentation for more details."
        ),
    )
    phase1_peaplabel: Optional[str] = Field(
        alias="phase1-peaplabel",
        default=NM_SETTING_8021X_DEFAULTS["phase1-peaplabel"],
        description=(
            "Forces use of the new PEAP label during key derivation. Some RADIUS servers may "
            "require forcing the new PEAP label to interoperate with PEAPv1. Set to \"1\" to force "
            "use of the new PEAP label. See the wpa_supplicant documentation for more details."
        ),
    )
    phase1_peapver: Optional[str] = Field(
        alias="phase1-peapver",
        default=NM_SETTING_8021X_DEFAULTS["phase1-peapver"],
        description=(
            "Forces which PEAP version is used when PEAP is set as the EAP method in the \"eap\" "
            "property. When unset, the version reported by the server will be used. Sometimes when "
            "using older RADIUS servers, it is necessary to force the client to use a particular "
            "PEAP version. To do so, this property may be set to \"0\" or \"1\" to force that "
            "specific PEAP version."
        ),
    )
    phase2_altsubject_matches: Optional[List[str]] = Field(
        alias="phase2-altsubject-matches",
        default=NM_SETTING_8021X_DEFAULTS["phase2-altsubject-matches"],
        description=(
            "List of strings to be matched against the altSubjectName of the certificate presented "
            "by the authentication server during the inner \"phase 2\" authentication. If the list "
            "is empty, no verification of the server certificate's altSubjectName is performed."
        ),
    )
    phase2_auth: Optional[str] = Field(
        alias="phase2-auth",
        default=NM_SETTING_8021X_DEFAULTS["phase2-auth"],
        description=(
            "Specifies the allowed \"phase 2\" inner authentication method when an EAP method that "
            "uses an inner TLS tunnel is specified in the \"eap\" property. For TTLS this property "
            "selects one of the supported non-EAP inner methods: \"pap\", \"chap\", \"mschap\", "
            "\"mschapv2\" while \"phase2-autheap\" selects an EAP inner method. For PEAP this "
            "selects an inner EAP method, one of: \"gtc\", \"otp\", \"md5\" and \"tls\". Each "
            "\"phase 2\" inner method requires specific parameters for successful authentication; "
            "see the wpa_supplicant documentation for more details. Both \"phase2-auth\" and "
            "\"phase2-autheap\" cannot be specified."
        ),
    )
    phase2_autheap: Optional[str] = Field(
        alias="phase2-autheap",
        default=NM_SETTING_8021X_DEFAULTS["phase2-autheap"],
        description=(
            "Specifies the allowed \"phase 2\" inner EAP-based authentication method when TTLS is "
            "specified in the \"eap\" property. Recognized EAP-based \"phase 2\" methods are "
            "\"md5\", \"mschapv2\", \"otp\", \"gtc\", and \"tls\". Each \"phase 2\" inner method "
            "requires specific parameters for successful authentication; see the wpa_supplicant "
            "documentation for more details."
        ),
    )
    phase2_ca_cert: Optional[str] = Field(
        alias="phase2-ca-cert",
        default=NM_SETTING_8021X_DEFAULTS["phase2-ca-cert"],
        description=(
            "Contains the \"phase 2\" CA certificate if used by the EAP method specified in the "
            "\"phase2-auth\" or \"phase2-autheap\" properties. Certificate data is specified using "
            "a \"scheme\"; three are currently supported: blob, path and pkcs#11 URL. When using "
            "the blob scheme this property should be set to the certificate's DER encoded data. "
            "When using the path scheme, this property should be set to the full UTF-8 encoded "
            "path of the certificate, prefixed with the string \"file://\" and ending with a "
            "terminating NUL byte. This property can be unset even if the EAP method supports CA "
            "certificates, but this allows man-in-the-middle attacks and is NOT recommended. Note "
            "that enabling NMSetting8021x:system-ca-certs will override this setting to use the "
            "built-in path, if the built-in path is not a directory.\n"
            "NOTE: In Summit RCM, this property always uses the path scheme and is expected to be "
            "the name of a previously-uploaded certificate (e.g. \"phase2-ca-cert.pem\")."
        ),
    )
    phase2_ca_cert_password: Optional[str] = Field(
        alias="phase2-ca-cert-password",
        default=NM_SETTING_8021X_DEFAULTS["phase2-ca-cert-password"],
        description=(
            "The password used to access the \"phase2\" CA certificate stored in "
            "\"phase2-ca-cert\" property. Only makes sense if the certificate is stored on a "
            "PKCS#11 token that requires a login."
        ),
    )
    phase2_ca_cert_password_flags: Optional[int] = Field(
        alias="phase2-ca-cert-password-flags",
        default=NM_SETTING_8021X_DEFAULTS["phase2-ca-cert-password-flags"],
        description=(
            "Flags indicating how to handle the \"phase2-ca-cert-password\" property."
        ),
    )
    phase2_ca_path: Optional[str] = Field(
        alias="phase2-ca-path",
        default=NM_SETTING_8021X_DEFAULTS["phase2-ca-path"],
        description=(
            "UTF-8 encoded path to a directory containing PEM or DER formatted certificates to be "
            "added to the verification chain in addition to the certificate specified in the "
            "\"phase2-ca-cert\" property. If NMSetting8021x:system-ca-certs is enabled and the "
            "built-in CA path is an existing directory, then this setting is ignored."
        ),
    )
    phase2_client_cert: Optional[str] = Field(
        alias="phase2-client-cert",
        default=NM_SETTING_8021X_DEFAULTS["phase2-client-cert"],
        description=(
            "Contains the \"phase 2\" client certificate if used by the EAP method specified in "
            "the \"phase2-auth\" or \"phase2-autheap\" properties. Certificate data is specified "
            "using a \"scheme\"; two are currently supported: blob and path. When using the blob "
            "scheme (which is backwards compatible with NM 0.7.x) this property should be set to "
            "the certificate's DER encoded data. When using the path scheme, this property should "
            "be set to the full UTF-8 encoded path of the certificate, prefixed with the string "
            "\"file://\" and ending with a terminating NUL byte. This property can be unset even "
            "if the EAP method supports CA certificates, but this allows man-in-the-middle attacks "
            "and is NOT recommended.\n"
            "NOTE: In Summit RCM, this property always uses the path scheme and is expected to be "
            "the name of a previously-uploaded certificate (e.g. \"phase2-client-cert.pem\")."
        ),
    )
    phase2_client_cert_password: Optional[str] = Field(
        alias="phase2-client-cert-password",
        default=NM_SETTING_8021X_DEFAULTS["phase2-client-cert-password"],
        description=(
            "The password used to access the \"phase2\" client certificate stored in "
            "\"phase2-client-cert\" property. Only makes sense if the certificate is stored on a "
            "PKCS#11 token that requires a login."
        ),
    )
    phase2_client_cert_password_flags: Optional[int] = Field(
        alias="phase2-client-cert-password-flags",
        default=NM_SETTING_8021X_DEFAULTS["phase2-client-cert-password-flags"],
        description=(
            "Flags indicating how to handle the \"phase2-client-cert-password\" property."
        ),
    )
    phase2_domain_match: Optional[str] = Field(
        alias="phase2-domain-match",
        default=NM_SETTING_8021X_DEFAULTS["phase2-domain-match"],
        description=(
            "Constraint for server domain name. If set, this list of FQDNs is used as a match "
            "requirement for dNSName element(s) of the certificate presented by the authentication "
            "server during the inner \"phase 2\" authentication. If a matching dNSName is found, "
            "this constraint is met. If no dNSName values are present, this constraint is matched "
            "against SubjectName CN using the same comparison. Multiple valid FQDNs can be passed "
            "as a \";\" delimited list."
        ),
    )
    phase2_domain_suffix_match: Optional[str] = Field(
        alias="phase2-domain-suffix-match",
        default=NM_SETTING_8021X_DEFAULTS["phase2-domain-suffix-match"],
        description=(
            "Constraint for server domain name. If set, this FQDN is used as a suffix match "
            "requirement for dNSName element(s) of the certificate presented by the authentication "
            "server during the inner \"phase 2\" authentication. If a matching dNSName is found, "
            "this constraint is met. If no dNSName values are present, this constraint is matched "
            "against SubjectName CN using same suffix match comparison. Since version 1.24, "
            "multiple valid FQDNs can be passed as a \";\" delimited list."
        ),
    )
    phase2_private_key: Optional[str] = Field(
        alias="phase2-private-key",
        default=NM_SETTING_8021X_DEFAULTS["phase2-private-key"],
        description=(
            "Contains the \"phase 2\" inner private key when the \"phase2-auth\" or "
            "\"phase2-autheap\" property is set to \"tls\". Key data is specified using a "
            "\"scheme\"; two are currently supported: blob and path. When using the blob scheme "
            "and private keys, this property should be set to the key's encrypted PEM encoded "
            "data. When using private keys with the path scheme, this property should be set to "
            "the full UTF-8 encoded path of the key, prefixed with the string \"file://\" and "
            "ending with a terminating NUL byte. When using PKCS#12 format private keys and the "
            "blob scheme, this property should be set to the PKCS#12 data and the "
            "\"phase2-private-key-password\" property must be set to password used to decrypt the "
            "PKCS#12 certificate and key. When using PKCS#12 files and the path scheme, this "
            "property should be set to the full UTF-8 encoded path of the key, prefixed with the "
            "string \"file://\" and ending with a terminating NUL byte, and as with the blob "
            "scheme the \"phase2-private-key-password\" property must be set to the password used "
            "to decode the PKCS#12 private key and certificate."
        ),
    )
    phase2_private_key_password: Optional[str] = Field(
        alias="phase2-private-key-password",
        default=NM_SETTING_8021X_DEFAULTS["phase2-private-key-password"],
        description=(
            "The password used to decrypt the \"phase 2\" private key specified in the "
            "\"phase2-private-key\" property when the private key either uses the path scheme, or "
            "is a PKCS#12 format key."
        ),
    )
    phase2_private_key_password_flags: Optional[int] = Field(
        alias="phase2-private-key-password-flags",
        default=NM_SETTING_8021X_DEFAULTS["phase2-private-key-password-flags"],
        description=(
            "Flags indicating how to handle the \"phase2-private-key-password\" property."
        ),
    )
    phase2_subject_match: Optional[str] = Field(
        alias="phase2-subject-match",
        default=NM_SETTING_8021X_DEFAULTS["phase2-subject-match"],
        description=(
            "Substring to be matched against the subject of the certificate presented by the "
            "authentication server during the inner \"phase 2\" authentication. When unset, no "
            "verification of the authentication server certificate's subject is performed. This "
            "property provides little security, if any, and should not be used. This property is "
            "deprecated since version 1.2. Use \"phase2-domain-suffix-match\" instead."
        ),
        deprecated=(
            "This property is deprecated since version 1.2. "
            "Use \"phase2-domain-suffix-match\" instead."
        ),
    )
    pin: Optional[str] = Field(
        default=NM_SETTING_8021X_DEFAULTS["pin"],
        description=(
            "PIN used for EAP authentication methods."
        ),
    )
    pin_flags: Optional[int] = Field(
        alias="pin-flags",
        default=NM_SETTING_8021X_DEFAULTS["pin-flags"],
        description=(
            "Flags indicating how to handle the \"pin\" property."
        ),
    )
    private_key: Optional[str] = Field(
        alias="private-key",
        default=NM_SETTING_8021X_DEFAULTS["private-key"],
        description=(
            "Contains the private key when the \"eap\" property is set to \"tls\". Key data is "
            "specified using a \"scheme\"; two are currently supported: blob and path. When using "
            "the blob scheme and private keys, this property should be set to the key's encrypted "
            "PEM encoded data. When using private keys with the path scheme, this property should "
            "be set to the full UTF-8 encoded path of the key, prefixed with the string "
            "\"file://\" and ending with a terminating NUL byte. When using PKCS#12 format private "
            "keys and the blob scheme, this property should be set to the PKCS#12 data and the "
            "\"private-key-password\" property must be set to password used to decrypt the PKCS#12 "
            "certificate and key. When using PKCS#12 files and the path scheme, this property "
            "should be set to the full UTF-8 encoded path of the key, prefixed with the string "
            "\"file://\" and ending with a terminating NUL byte, and as with the blob scheme the "
            "\"private-key-password\" property must be set to the password used to decode the "
            "PKCS#12 private key and certificate. WARNING: \"private-key\" is not a \"secret\" "
            "property, and thus unencrypted private key data using the BLOB scheme may be readable "
            "by unprivileged users. Private keys should always be encrypted with a private key "
            "password to prevent unauthorized access to unencrypted private key data.\n"
            "NOTE: In Summit RCM, this property always uses the path scheme and is expected to be "
            "the name of a previously-uploaded private key (e.g. \"private-key.pem\")."
        )
    )
    private_key_password: Optional[str] = Field(
        alias="private-key-password",
        default=NM_SETTING_8021X_DEFAULTS["private-key-password"],
        description=(
            "The password used to decrypt the private key specified in the \"private-key\" "
            "property when the private key either uses the path scheme, or if the private key is a "
            "PKCS#12 format key."
        ),
    )
    private_key_password_flags: Optional[int] = Field(
        alias="private-key-password-flags",
        default=NM_SETTING_8021X_DEFAULTS["private-key-password-flags"],
        description=(
            "Flags indicating how to handle the \"private-key-password\" property."
        ),
    )
    subject_match: Optional[str] = Field(
        alias="subject-match",
        default=NM_SETTING_8021X_DEFAULTS["subject-match"],
        description=(
            "Substring to be matched against the subject of the certificate presented by the "
            "authentication server. When unset, no verification of the authentication server "
            "certificate's subject is performed. This property provides little security, if any, "
            "and should not be used. This property is deprecated since version 1.2. Use "
            "\"phase2-domain-suffix-match\" instead."
        ),
        deprecated=(
            "This property is deprecated since version 1.2. "
            "Use \"phase2-domain-suffix-match\" instead."
        ),
    )
    system_ca_certs: Optional[bool] = Field(
        alias="system-ca-certs",
        default=NM_SETTING_8021X_DEFAULTS["system-ca-certs"],
        description=(
            "When TRUE, overrides the \"ca-path\" and \"phase2-ca-path\" properties using the "
            "system CA directory specified at configure time with the --system-ca-path switch. The "
            "certificates in this directory are added to the verification chain in addition to any "
            "certificates specified by the \"ca-cert\" and \"phase2-ca-cert\" properties. If the "
            "path provided with --system-ca-path is rather a file name (bundle of trusted CA "
            "certificates), it overrides \"ca-cert\" and \"phase2-ca-cert\" properties instead "
            "(sets ca_cert/ca_cert2 options for wpa_supplicant)."
        ),
    )


class ConnectionSettingsGsmModel(BaseModel):
    """Model for the 'gsm' setting of a NetworkManager Connection"""

    apn: Optional[str] = Field(
        default=NM_SETTING_GSM_DEFAULTS["apn"],
        description=(
            "The GPRS Access Point Name specifying the APN used when establishing a data session "
            "with the GSM-based network. The APN often determines how the user will be billed for "
            "their network usage and whether the user has access to the Internet or just a "
            "provider-specific walled-garden, so it is important to use the correct APN for the "
            "user's mobile broadband plan. The APN may only be composed of the characters a-z, "
            "0-9, ., and - per GSM 03.60 Section 14.9. If the APN is unset (the default) then it "
            "may be detected based on the \"auto-config\" setting. The property can be explicitly "
            "set to the empty string to prevent that and use no APN."
        ),
    )
    auto_config: Optional[bool] = Field(
        alias="auto-config",
        default=NM_SETTING_GSM_DEFAULTS["auto-config"],
        description=(
            "When TRUE, the settings such as APN, username, or password will default to values "
            "that match the network the modem will register to in the Mobile Broadband Provider "
            "database."
        ),
    )
    device_id: Optional[str] = Field(
        alias="device-id",
        default=NM_SETTING_GSM_DEFAULTS["device-id"],
        description=(
            "The device unique identifier (as given by the WWAN management service) which this "
            "connection applies to. If given, the connection will only apply to the specified "
            "device."
        ),
    )
    home_only: Optional[bool] = Field(
        alias="home-only",
        default=NM_SETTING_GSM_DEFAULTS["home-only"],
        description=(
            "When TRUE, only connections to the home network will be allowed. Connections to "
            "roaming networks will not be made."
        ),
    )
    initial_eps_bearer_apn: Optional[str] = Field(
        alias="initial-eps-bearer-apn",
        default=NM_SETTING_GSM_DEFAULTS["initial-eps-bearer-apn"],
        description=(
            "For LTE modems, this sets the APN for the initial EPS bearer that is set up when "
            "attaching to the network. Setting this parameter implies initial-eps-bearer-configure "
            "to be TRUE."
        ),
    )
    initial_eps_bearer_configure: Optional[bool] = Field(
        alias="initial-eps-bearer-configure",
        default=NM_SETTING_GSM_DEFAULTS["initial-eps-bearer-configure"],
        description=(
            "For LTE modems, this setting determines whether the initial EPS bearer shall be "
            "configured when bringing up the connection. It is inferred TRUE if "
            "initial-eps-bearer-apn is set."
        ),
    )
    initial_eps_bearer_noauth: Optional[bool] = Field(
        alias="initial-eps-bearer-noauth",
        default=NM_SETTING_GSM_DEFAULTS["initial-eps-bearer-noauth"],
        description=(
            "For LTE modems, this sets NOAUTH authentication method for the initial EPS bearer "
            "that is set up when attaching to the network. If TRUE, do not require the other side "
            "to authenticate itself to the client. If FALSE, require authentication from the "
            "remote side. In almost all cases, this should be TRUE."
        ),
    )
    initial_eps_bearer_password: Optional[str] = Field(
        alias="initial-eps-bearer-password",
        default=NM_SETTING_GSM_DEFAULTS["initial-eps-bearer-password"],
        description=(
            "For LTE modems, this sets the password for the initial EPS bearer that is set up when "
            "attaching to the network. Setting this parameter implies initial-eps-bearer-configure "
            "to be TRUE."
        ),
    )
    initial_eps_bearer_password_flags: Optional[int] = Field(
        alias="initial-eps-bearer-password-flags",
        default=NM_SETTING_GSM_DEFAULTS["initial-eps-bearer-password-flags"],
        description=(
            "Flags indicating how to handle the \"initial-eps-bearer-password\" property."
        ),
    )
    initial_eps_bearer_refuse_chap: Optional[bool] = Field(
        alias="initial-eps-bearer-refuse-chap",
        default=NM_SETTING_GSM_DEFAULTS["initial-eps-bearer-refuse-chap"],
        description=(
            "For LTE modems, this disables CHAP authentication method for the initial EPS bearer "
            "that is set up when attaching to the network."
        ),
    )
    initial_eps_bearer_refuse_eap: Optional[bool] = Field(
        alias="initial-eps-bearer-refuse-eap",
        default=NM_SETTING_GSM_DEFAULTS["initial-eps-bearer-refuse-eap"],
        description=(
            "For LTE modems, this disables EAP authentication method for the initial EPS bearer "
            "that is set up when attaching to the network."
        ),
    )
    initial_eps_bearer_refuse_mschap: Optional[bool] = Field(
        alias="initial-eps-bearer-refuse-mschap",
        default=NM_SETTING_GSM_DEFAULTS["initial-eps-bearer-refuse-mschap"],
        description=(
            "For LTE modems, this disables MSCHAP authentication method for the initial EPS bearer "
            "that is set up when attaching to the network."
        ),
    )
    initial_eps_bearer_refuse_mschapv2: Optional[bool] = Field(
        alias="initial-eps-bearer-refuse-mschapv2",
        default=NM_SETTING_GSM_DEFAULTS["initial-eps-bearer-refuse-mschapv2"],
        description=(
            "For LTE modems, this disables MSCHAPV2 authentication method for the initial EPS "
            "bearer that is set up when attaching to the network."
        ),
    )
    initial_eps_bearer_refuse_pap: Optional[bool] = Field(
        alias="initial-eps-bearer-refuse-pap",
        default=NM_SETTING_GSM_DEFAULTS["initial-eps-bearer-refuse-pap"],
        description=(
            "For LTE modems, this disables PAP authentication method for the initial EPS bearer "
            "that is set up when attaching to the network."
        ),
    )
    initial_eps_bearer_username: Optional[str] = Field(
        alias="initial-eps-bearer-username",
        default=NM_SETTING_GSM_DEFAULTS["initial-eps-bearer-username"],
        description=(
            "For LTE modems, this sets the username for the initial EPS bearer that is set up when "
            "attaching to the network. Setting this parameter implies initial-eps-bearer-configure "
            "to be TRUE."
        ),
    )
    mtu: Optional[int] = Field(
        default=NM_SETTING_GSM_DEFAULTS["mtu"],
        description=(
            "If non-zero, only transmit packets of the specified size or smaller, breaking larger "
            "packets up into multiple frames."
        ),
    )
    network_id: Optional[str] = Field(
        alias="network-id",
        default=NM_SETTING_GSM_DEFAULTS["network-id"],
        description=(
            "The Network ID (GSM LAI format, ie MCC-MNC) to force specific network registration. "
            "If the Network ID is specified, NetworkManager will attempt to force the device to "
            "register only on the specified network. This can be used to ensure that the device "
            "does not roam when direct roaming control of the device is not otherwise possible."
        ),
    )
    number: Optional[str] = Field(
        default=NM_SETTING_GSM_DEFAULTS["number"],
        description=(
            "Legacy setting that used to help establishing PPP data sessions for GSM-based modems. "
            "This property is deprecated since version 1.16. User-provided values for this setting "
            "are no longer used."
        ),
        deprecated=(
            "This property is deprecated since version 1.16. "
            "User-provided values for this setting are no longer used."
        ),
    )
    password: Optional[str] = Field(
        default=NM_SETTING_GSM_DEFAULTS["password"],
        description=(
            "The password used to authenticate with the network, if required. Many providers do "
            "not require a password, or accept any password. But if a password is required, it is "
            "specified here."
        ),
    )
    password_flags: Optional[int] = Field(
        alias="password-flags",
        default=NM_SETTING_GSM_DEFAULTS["password-flags"],
        description=(
            "Flags indicating how to handle the \"password\" property."
        ),
    )
    pin: Optional[str] = Field(
        default=NM_SETTING_GSM_DEFAULTS["pin"],
        description=(
            "If the SIM is locked with a PIN it must be unlocked before any other operations are "
            "requested. Specify the PIN here to allow operation of the device."
        ),
    )
    pin_flags: Optional[int] = Field(
        alias="pin-flags",
        default=NM_SETTING_GSM_DEFAULTS["pin-flags"],
        description=(
            "Flags indicating how to handle the \"pin\" property."
        ),
    )
    sim_id: Optional[str] = Field(
        alias="sim-id",
        default=NM_SETTING_GSM_DEFAULTS["sim-id"],
        description=(
            "The SIM card unique identifier (as given by the WWAN management service) which this "
            "connection applies to. If given, the connection will apply to any device also allowed "
            "by \"device-id\" which contains a SIM card matching the given identifier."
        ),
    )
    sim_operator_id: Optional[str] = Field(
        alias="sim-operator-id",
        default=NM_SETTING_GSM_DEFAULTS["sim-operator-id"],
        description=(
            "A MCC/MNC string like \"310260\" or \"21601\" identifying the specific mobile network "
            "operator which this connection applies to. If given, the connection will apply to any "
            "device also allowed by \"device-id\" and \"sim-id\" which contains a SIM card "
            "provisioned by the given operator."
        ),
    )
    username: Optional[str] = Field(
        default=NM_SETTING_GSM_DEFAULTS["username"],
        description=(
            "The username used to authenticate with the network, if required. Many providers do "
            "not require a username, or accept any username. But if a username is required, it is "
            "specified here."
        ),
    )


class ConnectionSettingsIPConfigModel(BaseModel):
    """Base model for an IP config setting of a NetworkManager Connection"""

    address_data: Optional[List[Dict]] = Field(
        alias="address-data",
        default=NM_SETTING_IPCONFIG_DEFAULTS["address-data"],
        description=(
            "Array of IPv4 addresses. Each address dictionary contains at least 'address' and "
            "'prefix' entries, containing the IP address as a string, and the prefix length as a "
            "uint32. Additional attributes may also exist on some addresses."
        )
    )
    addresses: Optional[List[str]] = Field(
        default=NM_SETTING_IPCONFIG_DEFAULTS["addresses"],
        description=(
            "Deprecated in favor of the 'address-data' and 'gateway' properties, but this can be "
            "used for backward-compatibility with older daemons. Note that if you send this "
            "property the daemon will ignore 'address-data' and 'gateway'. Array of IPv4 address "
            "structures. Each IPv4 address structure is composed of 3 32-bit values; the first "
            "being the IPv4 address (network byte order), the second the prefix (1 - 32), and last "
            "the IPv4 gateway (network byte order). The gateway may be left as 0 if no gateway "
            "exists for that subnet."
        ),
        deprecated=True,
    )
    auto_route_ext_gw: Optional[int] = Field(
        alias="auto-route-ext-gw",
        default=NM_SETTING_IPCONFIG_DEFAULTS["auto-route-ext-gw"],
        description=(
            "VPN connections will default to add the route automatically unless this setting is "
            "set to FALSE. For other connection types, adding such an automatic route is currently "
            "not supported and setting this to TRUE has no effect."
        ),
    )
    dad_timeout: Optional[int] = Field(
        alias="dad-timeout",
        default=NM_SETTING_IPCONFIG_DEFAULTS["dad-timeout"],
        description=(
            "Maximum timeout in milliseconds used to check for the presence of duplicate IP "
            "addresses on the network. If an address conflict is detected, the activation will "
            "fail. The property is currently implemented only for IPv4. A zero value means that no "
            "duplicate address detection is performed, -1 means the default value (either the "
            "value configured globally in NetworkManger.conf or 200ms). A value greater than zero "
            "is a timeout in milliseconds. Note that the time intervals are subject to "
            "randomization as per RFC 5227 and so the actual duration can be between half and the "
            "full time specified in this property."
        ),
    )
    dhcp_dscp: Optional[str] = Field(
        alias="dhcp-dscp",
        default=NM_SETTING_IPCONFIG_DEFAULTS["dhcp-dscp"],
        description=(
            "Specifies the value for the DSCP field (traffic class) of the IP header. When empty, "
            "the global default value is used; if no global default is specified, it is assumed to "
            "be \"CS0\". Allowed values are: \"CS0\", \"CS4\" and \"CS6\". The property is "
            "currently valid only for IPv4, and it is supported only by the \"internal\" DHCP "
            "plugin."
        ),
    )
    dhcp_hostname: Optional[str] = Field(
        alias="dhcp-hostname",
        default=NM_SETTING_IPCONFIG_DEFAULTS["dhcp-hostname"],
        description=(
            "If the \"dhcp-send-hostname\" property is TRUE, then the specified name will be sent "
            "to the DHCP server when acquiring a lease. This property and \"dhcp-fqdn\" are "
            "mutually exclusive and cannot be set at the same time."
        ),
    )
    dhcp_hostname_flags: Optional[int] = Field(
        alias="dhcp-hostname-flags",
        default=NM_SETTING_IPCONFIG_DEFAULTS["dhcp-hostname-flags"],
        description=(
            "Flags for the DHCP hostname and FQDN. Currently, this property only includes flags to "
            "control the FQDN flags set in the DHCP FQDN option. Supported FQDN flags are 0x1 "
            "(fqdn-serv-update), 0x2 (fqdn-encoded) and 0x4 (fqdn-no-update). When no FQDN flag is "
            "set and 0x8 (fqdn-clear-flags) is set, the DHCP FQDN option will contain no flag. "
            "Otherwise, if no FQDN flag is set and 0x8 (fqdn-clear-flags) is not set, the standard "
            "FQDN flags are set in the request: 0x1 (fqdn-serv-update), 0x2 (fqdn-encoded) for "
            "IPv4 and 0x1 (fqdn-serv-update) for IPv6. When this property is set to the default "
            "value 0x0 (none), a global default is looked up in NetworkManager configuration. If "
            "that value is unset or also 0x0 (none), then the standard FQDN flags described above "
            "are sent in the DHCP requests."
        ),
    )
    dhcp_iaid: Optional[str] = Field(
        alias="dhcp-iaid",
        default=NM_SETTING_IPCONFIG_DEFAULTS["dhcp-iaid"],
        description=(
            "A string containing the \"Identity Association Identifier\" (IAID) used by the DHCP "
            "client. The string can be a 32-bit number (either decimal, hexadecimal or as colon "
            "separated hexadecimal numbers). Alternatively it can be set to the special values "
            "\"mac\", \"perm-mac\", \"ifname\" or \"stable\". When set to \"mac\" (or "
            "\"perm-mac\"), the last 4 bytes of the current (or permanent) MAC address are used as "
            "IAID. When set to \"ifname\", the IAID is computed by hashing the interface name. The "
            "special value \"stable\" can be used to generate an IAID based on the stable-id (see "
            "connection.stable-id), a per-host key and the interface name. When the property is "
            "unset, the value from global configuration is used; if no global default is set then "
            "the IAID is assumed to be \"ifname\". For DHCPv4, the IAID is only used with "
            "\"ipv4.dhcp-client-id\" values \"duid\" and \"ipv6-duid\" to generate the client-id. "
            "For DHCPv6, note that at the moment this property is only supported by the "
            "\"internal\" DHCPv6 plugin. The \"dhclient\" DHCPv6 plugin always derives the IAID "
            "from the MAC address. The actually used DHCPv6 IAID for a currently activated "
            "interface is exposed in the lease information of the device."
        ),
    )
    dhcp_reject_servers: Optional[List[str]] = Field(
        alias="dhcp-reject-servers",
        default=NM_SETTING_IPCONFIG_DEFAULTS["dhcp-reject-servers"],
        description=(
            "Array of servers from which DHCP offers must be rejected. This property is useful to "
            "avoid getting a lease from misconfigured or rogue servers. For DHCPv4, each element "
            "must be an IPv4 address, optionally followed by a slash and a prefix length (e.g. "
            "\"192.168.122.0/24\"). This property is currently not implemented for DHCPv6."
        ),
    )
    dhcp_send_hostname: Optional[bool] = Field(
        alias="dhcp-send-hostname",
        default=NM_SETTING_IPCONFIG_DEFAULTS["dhcp-send-hostname"],
        description=(
            "Since 1.52 this property is deprecated and is only used as fallback value for "
            "\"dhcp-send-hostname-v2\" if it's set to 'default'. This is only done to avoid "
            "breaking existing configurations, the new property should be used from now on. This "
            "property is deprecated since version 1.52. Use the new version of dhcp-send-hostname "
            "instead."
        ),
        deprecated=(
            "This property is deprecated since version 1.52. "
            "Use the new version of \"dhcp-send-hostname\" instead."
        ),
    )
    dhcp_send_hostname_v2: Optional[int] = Field(
        alias="dhcp-send-hostname-v2",
        default=NM_SETTING_IPCONFIG_DEFAULTS["dhcp-send-hostname-v2"],
        description=(
            "If TRUE, a hostname is sent to the DHCP server when acquiring a lease. Some DHCP "
            "servers use this hostname to update DNS databases, essentially providing a static "
            "hostname for the computer. If the \"dhcp-hostname\" property is NULL and this "
            "property is TRUE, the current persistent hostname of the computer is sent. The "
            "default value is -1 (default). In this case the global value from NetworkManager "
            "configuration is looked up. If it's not set, the value from \"dhcp-send-hostname\", "
            "which defaults to TRUE, is used for backwards compatibility. In the future this will "
            "change and, in absence of a global default, it will always fallback to TRUE."
        ),
    )
    dhcp_send_release: Optional[int] = Field(
        alias="dhcp-send-release",
        default=NM_SETTING_IPCONFIG_DEFAULTS["dhcp-send-release"],
        description=(
            "Whether the DHCP client will send RELEASE message when bringing the connection down. "
            "The default value is -1 (default). When the default value is specified, then the "
            "global value from NetworkManager configuration is looked up, if not set, it is "
            "considered as FALSE."
        ),
    )
    dhcp_timeout: Optional[int] = Field(
        alias="dhcp-timeout", 
        default=NM_SETTING_IPCONFIG_DEFAULTS["dhcp-timeout"],
        description=(
            "A timeout for a DHCP transaction in seconds. If zero (the default), a globally "
            "configured default is used. If still unspecified, a device specific timeout is used "
            "(usually 45 seconds). Set to 2147483647 (MAXINT32) for infinity."
        ),
    )
    dns: Optional[List[str]] = Field(
        default=NM_SETTING_IPCONFIG_DEFAULTS["dns"],
        description=(
            "Array of IP addresses of DNS servers"
        ),
        deprecated=True,
    )
    dns_data: Optional[List[str]] = Field(
        alias="dns-data",
        default=NM_SETTING_IPCONFIG_DEFAULTS["dns-data"],
        description=(
            "Array of DNS name servers. This replaces the deprecated \"dns\" property. Each name "
            "server can also contain a DoT server name."
        ),
    )
    dns_options: Optional[List[str]] = Field(
        alias="dns-options",
        default=NM_SETTING_IPCONFIG_DEFAULTS["dns-options"],
        description=(
            "Array of DNS options to be added to resolv.conf. NULL means that the options are "
            "unset and left at the default. In this case NetworkManager will use default options. "
            "This is distinct from an empty list of properties. The following options are directly "
            "added to resolv.conf: \"attempts\", \"debug\", \"edns0\", \"inet6\", "
            "\"ip6-bytestring\", \"ip6-dotint\", \"ndots\", \"no-aaaa\", \"no-check-names\", "
            "\"no-ip6-dotint\", \"no-reload\", \"no-tld-query\", \"rotate\", \"single-request\", "
            "\"single-request-reopen\", \"timeout\", \"trust-ad\", \"use-vc\". See the "
            "resolv.conf(5) man page for a detailed description of these options. In addition, "
            "NetworkManager supports the special options \"_no-add-edns0\" and "
            "\"_no-add-trust-ad\". They are not added to resolv.conf, and can be used to prevent "
            "the automatic addition of options \"edns0\" and \"trust-ad\" when using caching DNS "
            "plugins (see below). The \"trust-ad\" setting is only honored if the profile "
            "contributes name servers to resolv.conf, and if all contributing profiles have "
            "\"trust-ad\" enabled. When using a caching DNS plugin (dnsmasq or systemd-resolved in "
            "NetworkManager.conf) then \"edns0\" and \"trust-ad\" are automatically added, unless "
            "\"_no-add-edns0\" and \"_no-add-trust-ad\" are present."
        ),
    )
    dns_priority: Optional[int] = Field(
        alias="dns-priority",
        default=NM_SETTING_IPCONFIG_DEFAULTS["dns-priority"],
        description=(
            "DNS servers priority. The relative priority for DNS servers specified by this "
            "setting. A lower numerical value is better (higher priority). Negative values have "
            "the special effect of excluding other configurations with a greater numerical "
            "priority value; so in presence of at least one negative priority, only DNS servers "
            "from connections with the lowest priority value will be used. To avoid all DNS leaks, "
            "set the priority of the profile that should be used to the most negative value of all "
            "active connections profiles. Zero selects a globally configured default value. If the "
            "latter is missing or zero too, it defaults to 50 for VPNs (including WireGuard) and "
            "100 for other connections. Note that the priority is to order DNS settings for "
            "multiple active connections. It does not disambiguate multiple DNS servers within the "
            "same connection profile. When multiple devices have configurations with the same "
            "priority, VPNs will be considered first, then devices with the best (lowest metric) "
            "default route and then all other devices. When using dns=default, servers with higher "
            "priority will be on top of resolv.conf. To prioritize a given server over another one "
            "within the same connection, just specify them in the desired order. Note that "
            "commonly the resolver tries name servers in /etc/resolv.conf in the order listed, "
            "proceeding with the next server in the list on failure. See for example the "
            "\"rotate\" option of the dns-options setting. If there are any negative DNS "
            "priorities, then only name servers from the devices with that lowest priority will be "
            "considered. When using a DNS resolver that supports Conditional Forwarding or Split "
            "DNS (with dns=dnsmasq or dns=systemd-resolved settings), each connection is used to "
            "query domains in its search list. The search domains determine which name servers to "
            "ask, and the DNS priority is used to prioritize name servers based on the domain. "
            "Queries for domains not present in any search list are routed through connections "
            "having the '~.' special wildcard domain, which is added automatically to connections "
            "with the default route (or can be added manually). When multiple connections specify "
            "the same domain, the one with the best priority (lowest numerical value) wins. If a "
            "sub domain is configured on another interface it will be accepted regardless the "
            "priority, unless parent domain on the other interface has a negative priority, which "
            "causes the sub domain to be shadowed. With Split DNS one can avoid undesired DNS "
            "leaks by properly configuring DNS priorities and the search domains, so that only "
            "name servers of the desired interface are configured."
        ),
    )
    dns_search: Optional[List[str]] = Field(
        alias="dns-search",
        default=NM_SETTING_IPCONFIG_DEFAULTS["dns-search"],
        description=(
            "List of DNS search domains. Domains starting with a tilde ('~') are considered "
            "'routing' domains and are used only to decide the interface over which a query must "
            "be forwarded; they are not used to complete unqualified host names. When using a DNS "
            "plugin that supports Conditional Forwarding or Split DNS, then the search domains "
            "specify which name servers to query. This makes the behavior different from running "
            "with plain /etc/resolv.conf. For more information see also the dns-priority setting. "
            "When set on a profile that also enabled DHCP, the DNS search list received "
            "automatically (option 119 for DHCPv4 and option 24 for DHCPv6) gets merged with the "
            "manual list. This can be prevented by setting \"ignore-auto-dns\". Note that if no "
            "DNS searches are configured, the fallback will be derived from the domain from DHCP "
            "(option 15)."
        ),
    )
    gateway: Optional[str] = Field(
        default=NM_SETTING_IPCONFIG_DEFAULTS["gateway"],
        description=(
            "The gateway associated with this configuration. This is only meaningful if "
            "\"addresses\" is also set. Setting the gateway causes NetworkManager to configure a "
            "standard default route with the gateway as next hop. This is ignored if "
            "\"never-default\" is set. An alternative is to configure the default route explicitly "
            "with a manual route and /0 as prefix length. Note that the gateway usually conflicts "
            "with routing that NetworkManager configures for WireGuard interfaces, so usually it "
            "should not be set in that case. See \"ip4-auto-default-route\"."
        )
    )
    ignore_auto_dns: Optional[bool] = Field(
        alias="ignore-auto-dns",
        default=NM_SETTING_IPCONFIG_DEFAULTS["ignore-auto-dns"],
        description=(
            "When \"method\" is set to \"auto\" and this property to TRUE, automatically "
            "configured name servers and search domains are ignored and only name servers and "
            "search domains specified in the \"dns\" and \"dns-search\" properties, if any, are "
            "used."
        ),
    )
    ignore_auto_routes: Optional[bool] = Field(
        alias="ignore-auto-routes",
        default=NM_SETTING_IPCONFIG_DEFAULTS["ignore-auto-routes"],
        description=(
            "When \"method\" is set to \"auto\" and this property to TRUE, automatically "
            "configured routes are ignored and only routes specified in the \"routes\" property, "
            "if any, are used."
        ),
    )
    may_fail: Optional[bool] = Field(
        alias="may-fail",
        default=NM_SETTING_IPCONFIG_DEFAULTS["may-fail"],
        description=(
            "If TRUE, allow overall network configuration to proceed even if the configuration "
            "specified by this property times out. Note that at least one IP configuration must "
            "succeed or overall network configuration will still fail. For example, in IPv6-only "
            "networks, setting this property to TRUE on the NMSettingIP4Config allows the overall "
            "network configuration to succeed if IPv4 configuration fails but IPv6 configuration "
            "completes successfully."
        ),
    )
    method: Optional[str] = Field(
        default=NM_SETTING_IPCONFIG_DEFAULTS["method"],
        description=(
            "IP configuration method. NMSettingIP4Config and NMSettingIP6Config both support "
            "\"disabled\", \"auto\", \"manual\", and \"link-local\". See the subclass-specific "
            "documentation for other values. In general, for the \"auto\" method, properties such "
            "as \"dns\" and \"routes\" specify information that is added on to the information "
            "returned from automatic configuration. The \"ignore-auto-routes\" and "
            "\"ignore-auto-dns\" properties modify this behavior. For methods that imply no "
            "upstream network, such as \"shared\" or \"link-local\", these properties must be "
            "empty. For IPv4 method \"shared\", the IP subnet can be configured by adding one "
            "manual IPv4 address or otherwise 10.42.x.0/24 is chosen. Note that the shared method "
            "must be configured on the interface which shares the internet to a subnet, not on the "
            "uplink which is shared."
        ),
    )
    never_default: Optional[bool] = Field(
        alias="never-default",
        default=NM_SETTING_IPCONFIG_DEFAULTS["never-default"],
        description=(
            "If TRUE, this connection will never be the default connection for this IP type, "
            "meaning it will never be assigned the default route by NetworkManager."
        ),
    )
    replace_local_rule: Optional[int] = Field(
        alias="replace-local-rule",
        default=NM_SETTING_IPCONFIG_DEFAULTS["replace-local-rule"],
        description=(
            "Connections will default to keep the autogenerated priority 0 local rule unless this "
            "setting is set to TRUE."
        ),
    )
    required_timeout: Optional[int] = Field(
        alias="required-timeout",
        default=NM_SETTING_IPCONFIG_DEFAULTS["required-timeout"],
        description=(
            "The minimum time interval in milliseconds for which dynamic IP configuration should "
            "be tried before the connection succeeds. This property is useful for example if both "
            "IPv4 and IPv6 are enabled and are allowed to fail. Normally the connection succeeds "
            "as soon as one of the two address families completes; by setting a required timeout "
            "for e.g. IPv4, one can ensure that even if IP6 succeeds earlier than IPv4, "
            "NetworkManager waits some time for IPv4 before the connection becomes active. Note "
            "that if \"may-fail\" is FALSE for the same address family, this property has no "
            "effect as NetworkManager needs to wait for the full DHCP timeout. A zero value means "
            "that no required timeout is present, -1 means the default value (either configuration "
            "ipvx.required-timeout override or zero)."
        ),
    )
    route_data: Optional[List[Dict]] = Field(
        alias="route-data",
        default=NM_SETTING_IPCONFIG_DEFAULTS["route-data"],
        description=(
            "Array of IPv4 routes. Each route dictionary contains at least 'dest' and 'prefix' "
            "entries, containing the destination IP address as a string, and the prefix length as "
            "a uint32. Most routes will also have a 'next-hop' entry, containing the next hop IP "
            "address as a string. If the route has a 'metric' entry (containing a uint32), that "
            "will be used as the metric for the route (otherwise NM will pick a default value "
            "appropriate to the device). Additional attributes may also exist on some routes."
        ),
    )
    route_metric: Optional[int] = Field(
        alias="route-metric",
        default=NM_SETTING_IPCONFIG_DEFAULTS["route-metric"],
        description=(
            "The default metric for routes that don't explicitly specify a metric. The default "
            "value -1 means that the metric is chosen automatically based on the device type. The "
            "metric applies to dynamic routes, manual (static) routes that don't have an explicit "
            "metric setting, address prefix routes, and the default route. Note that for IPv6, the "
            "kernel accepts zero (0) but coerces it to 1024 (user default). Hence, setting this "
            "property to zero effectively mean setting it to 1024. For IPv4, zero is a regular "
            "value for the metric."
        ),
    )
    route_table: Optional[int] = Field(
        alias="route-table",
        default=NM_SETTING_IPCONFIG_DEFAULTS["route-table"],
        description=(
            "Enable policy routing (source routing) and set the routing table used when adding "
            "routes. This affects all routes, including device-routes, IPv4LL, DHCP, SLAAC, "
            "default-routes and static routes. But note that static routes can individually "
            "overwrite the setting by explicitly specifying a non-zero routing table. If the table "
            "setting is left at zero, it is eligible to be overwritten via global configuration. "
            "If the property is zero even after applying the global configuration value, policy "
            "routing is disabled for the address family of this connection. Policy routing "
            "disabled means that NetworkManager will add all routes to the main table (except "
            "static routes that explicitly configure a different table). Additionally, "
            "NetworkManager will not delete any extraneous routes from tables except the main "
            "table. This is to preserve backward compatibility for users who manage routing tables "
            "outside of NetworkManager."
        ),
    )
    routed_dns: Optional[int] = Field(
        alias="routed-dns",
        default=NM_SETTING_IPCONFIG_DEFAULTS["routed-dns"],
        description=(
            "Whether to add routes for DNS servers. When enabled, NetworkManager adds a route for "
            "each DNS server that is associated with this connection either statically (defined in "
            "the connection profile) or dynamically (for example, retrieved via DHCP). The route "
            "guarantees that the DNS server is reached via this interface. When set to -1 "
            "(default), the value from global configuration is used; if no global default is "
            "defined, this feature is disabled."
        ),
    )
    routes: Optional[List[str]] = Field(
        default=NM_SETTING_IPCONFIG_DEFAULTS["routes"],
        description=(
            "Deprecated in favor of the 'route-data' property, but this can be used for "
            "backward-compatibility with older daemons. Note that if you send this property the "
            "daemon will ignore 'route-data'. Array of IPv4 route structures. Each IPv4 route "
            "structure is composed of 4 32-bit values; the first being the destination IPv4 "
            "network or address (network byte order), the second the destination network or "
            "address prefix (1 - 32), the third being the next-hop (network byte order) if any, "
            "and the fourth being the route metric. If the metric is 0, NM will choose an "
            "appropriate default metric for the device. (There is no way to explicitly specify an "
            "actual metric of 0 with this property.)"
        ),
        deprecated=True,
    )
    routing_rules: Optional[List[Dict]] = Field(
        alias="routing-rules",
        default=NM_SETTING_IPCONFIG_DEFAULTS["routing-rules"],
        description=(
            "Array of dictionaries for routing rules. Each routing rule supports the following "
            "options: action (y), dport-end (q), dport-start (q), family (i), from (s), "
            "from-len (y), fwmark (u), fwmask (u), iifname (s), invert (b), ipproto (s), "
            "oifname (s), priority (u), sport-end (q), sport-start (q), supress-prefixlength (i), "
            "table (u), to (s), tos (y), to-len (y), range-end (u), range-start (u)."
        ),
    )
    shared_dhcp_lease_time: Optional[int] = Field(
        alias="shared-dhcp-lease-time",
        default=NM_SETTING_IPCONFIG_DEFAULTS["shared-dhcp-lease-time"],
        description=(
            "This option allows you to specify a custom DHCP lease time for the shared connection "
            "method in seconds. The value should be either a number between 120 and 31536000 (one "
            "year). If this option is not specified, 3600 (one hour) is used. Special values are 0 "
            "for default value of 1 hour and 2147483647 (MAXINT32) for infinite lease time."
        ),
    )
    shared_dhcp_range: Optional[str] = Field(
        alias="shared-dhcp-range",
        default=NM_SETTING_IPCONFIG_DEFAULTS["shared-dhcp-range"],
        description=(
            "This option allows you to specify a custom DHCP range for the shared connection "
            "method. The value is expected to be in `<START_ADDRESS>,<END_ADDRESS>` format. The "
            "range should be part of network set by ipv4.address option and it should not contain "
            "network address or broadcast address. If this option is not specified, the DHCP range "
            "will be automatically determined based on the interface address. The range will be "
            "selected to be adjacent to the interface address, either before or after it, with the "
            "larger possible range being preferred. The range will be adjusted to fill the "
            "available address space, except for networks with a prefix length greater than 24, "
            "which will be treated as if they have a prefix length of 24."
        ),
    )


class ConnectionSettingsIP4ConfigModel(ConnectionSettingsIPConfigModel):
    """Model for the 'ipv4' setting of a NetworkManager Connection"""

    dhcp_client_id: Optional[str] = Field(
        alias="dhcp-client-id",
        default=NM_SETTING_IP4CONFIG_DEFAULTS["dhcp-client-id"],
        description=(
            "A string sent to the DHCP server to identify the local machine which the DHCP server "
            "may use to customize the DHCP lease and options. When the property is a hex string "
            "('aa:bb:cc') it is interpreted as a binary client ID, in which case the first byte is "
            "assumed to be the 'type' field as per RFC 2132 section 9.14 and the remaining bytes "
            "may be an hardware address (e.g. '01:xx:xx:xx:xx:xx:xx' where 1 is the Ethernet ARP "
            "type and the rest is a MAC address). If the property is not a hex string it is "
            "considered as a non-hardware-address client ID and the 'type' field is set to 0. The "
            "special values \"mac\" and \"perm-mac\" are supported, which use the current or "
            "permanent MAC address of the device to generate a client identifier with type "
            "ethernet (01). Currently, these options only work for ethernet type of links. The "
            "special value \"ipv6-duid\" uses the DUID from \"ipv6.dhcp-duid\" property as an "
            "RFC4361-compliant client identifier. As IAID it uses \"ipv4.dhcp-iaid\" and falls "
            "back to \"ipv6.dhcp-iaid\" if unset. The special value \"duid\" generates a "
            "RFC4361-compliant client identifier based on \"ipv4.dhcp-iaid\" and uses a DUID "
            "generated by hashing /etc/machine-id. The special value \"stable\" is supported to "
            "generate a type 0 client identifier based on the stable-id (see connection.stable-id) "
            "and a per-host key. If you set the stable-id, you may want to include the "
            "\"${DEVICE}\" or \"${MAC}\" specifier to get a per-device key. The special value "
            "\"none\" prevents any client identifier from being sent. Note that this is normally "
            "not recommended. If unset, a globally configured default from NetworkManager.conf is "
            "used. If still unset, the default depends on the DHCP plugin. The internal dhcp "
            "client will default to \"mac\" and the dhclient plugin will try to use one from its "
            "config file if present, or won't sent any client-id otherwise."
        )
    )
    dhcp_fqdn: Optional[str] = Field(
        alias="dhcp-fqdn",
        default=NM_SETTING_IP4CONFIG_DEFAULTS["dhcp-fqdn"],
        description=(
            "If the \"dhcp-send-hostname\" property is TRUE, then the specified FQDN will be sent "
            "to the DHCP server when acquiring a lease. This property and \"dhcp-hostname\" are "
            "mutually exclusive and cannot be set at the same time."
        ),
    )
    dhcp_ipv6_only_preferred: Optional[int] = Field(
        alias="dhcp-ipv6-only-preferred",
        default=NM_SETTING_IP4CONFIG_DEFAULTS["dhcp-ipv6-only-preferred"],
        description=(
            "Controls the \"IPv6-Only Preferred\" DHCPv4 option (RFC 8925). When set to 1 (yes), "
            "the host adds the option to the parameter request list; if the DHCP server sends the "
            "option back, the host stops the DHCP client for the time interval specified in the "
            "option. Enable this feature if the host supports an IPv6-only mode, i.e. either all "
            "applications are IPv6-only capable or there is a form of 464XLAT deployed. When set "
            "to -1 (default), the actual value is looked up in the global configuration; if not "
            "specified, it defaults to 0 (no). If the connection has IPv6 method set to "
            "\"disabled\", this property does not have effect and the \"IPv6-Only Preferred\" "
            "option is always disabled."
        ),
    )
    dhcp_vendor_class_identifier: Optional[str] = Field(
        alias="dhcp-vendor-class-identifier",
        default=NM_SETTING_IP4CONFIG_DEFAULTS["dhcp-vendor-class-identifier"],
        description=(
            "The Vendor Class Identifier DHCP option (60). Special characters in the data string "
            "may be escaped using C-style escapes, nevertheless this property cannot contain nul "
            "bytes. If the per-profile value is unspecified (the default), a global connection "
            "default gets consulted. If still unspecified, the DHCP option is not sent to the "
            "server."
        ),
    )
    link_local: Optional[int] = Field(
        alias="link-local",
        default=NM_SETTING_IP4CONFIG_DEFAULTS["link-local"],
        description=(
            "Enable and disable the IPv4 link-local configuration independently of the ipv4.method "
            "configuration. This allows a link-local address (169.254.x.y/16) to be obtained in "
            "addition to other addresses, such as those manually configured or obtained from a "
            "DHCP server. When set to \"auto\", the value is dependent on \"ipv4.method\". When "
            "set to \"default\", it honors the global connection default, before falling back to "
            "\"auto\". Note that if \"ipv4.method\" is \"disabled\", then link local addressing is "
            "always disabled too. The default is \"default\". Since 1.52, when set to "
            "\"fallback\", a link-local address is obtained if no other IPv4 address is set."
        ),
    )


class ConnectionSettingsIP6ConfigModel(ConnectionSettingsIPConfigModel):
    """Model for the 'ipv6' setting of a NetworkManager Connection"""

    addr_gen_mode: Optional[int] = Field(
        alias="addr-gen-mode",
        default=NM_SETTING_IP6CONFIG_DEFAULTS["addr-gen-mode"],
        description=(
            "Configure the method for creating the IPv6 interface identifier of addresses for "
            "RFC4862 IPv6 Stateless Address Autoconfiguration and IPv6 Link Local. The permitted "
            "values are: 0 (eui64), 1 (stable-privacy). 2 (default-or-eui64) or 3 (default). If "
            "the property is set to \"eui64\", the addresses will be generated using the interface "
            "token derived from the hardware address. This makes the host part of the address "
            "constant, making it possible to track the host's presence when it changes networks. "
            "The address changes when the interface hardware is replaced. If a duplicate address "
            "is detected, there is no fallback to generate another address. When configured, the "
            "\"ipv6.token\" is used instead of the MAC address to generate addresses for stateless "
            "autoconfiguration. If the property is set to \"stable-privacy\", the interface "
            "identifier is generated as specified by RFC7217. This works by hashing a host "
            "specific key (see NetworkManager(8) manual), the interface name, the connection's "
            "\"connection.stable-id\" property and the address prefix. This improves privacy by "
            "making it harder to use the address to track the host's presence as every prefix and "
            "network has a different identifier. Also, the address is stable when the network "
            "interface hardware is replaced. The special values \"default\" and "
            "\"default-or-eui64\" will fallback to the global connection default as documented in "
            "the NetworkManager.conf(5) manual. If the global default is not specified, the "
            "fallback value is \"stable-privacy\" or \"eui64\", respectively. For libnm, the "
            "property defaults to \"default\" since 1.40. Previously it used to default to "
            "\"stable-privacy\". On D-Bus, the absence of an addr-gen-mode setting equals "
            "\"default\". For keyfile plugin, the absence of the setting on disk means "
            "\"default-or-eui64\" so that the property doesn't change on upgrade from older "
            "versions. Note that this setting is distinct from the Privacy Extensions as "
            "configured by \"ip6-privacy\" property and it does not affect the temporary addresses "
            "configured with this option."
        ),
    )
    dhcp_duid: Optional[str] = Field(
        alias="dhcp-duid",
        default=NM_SETTING_IP6CONFIG_DEFAULTS["dhcp-duid"],
        description=(
            "A string containing the DHCPv6 Unique Identifier (DUID) used by the dhcp client to "
            "identify itself to DHCPv6 servers (RFC 3315). The DUID is carried in the Client "
            "Identifier option. If the property is a hex string ('aa:bb:cc') it is interpreted as "
            "a binary DUID and filled as an opaque value in the Client Identifier option. The "
            "special value \"lease\" will retrieve the DUID previously used from the lease file "
            "belonging to the connection. If no DUID is found and \"dhclient\" is the configured "
            "dhcp client, the DUID is searched in the system-wide dhclient lease file. If still no "
            "DUID is found, or another dhcp client is used, a global and permanent DUID-UUID (RFC "
            "6355) will be generated based on the machine-id. The special values \"llt\" and "
            "\"ll\" will generate a DUID of type LLT or LL (see RFC 3315) based on the current MAC "
            "address of the device. In order to try providing a stable DUID-LLT, the time field "
            "will contain a constant timestamp that is used globally (for all profiles) and "
            "persisted to disk. The special values \"stable-llt\", \"stable-ll\" and "
            "\"stable-uuid\" will generate a DUID of the corresponding type, derived from the "
            "connection's stable-id and a per-host unique key. You may want to include the "
            "\"${DEVICE}\" or \"${MAC}\" specifier in the stable-id, in case this profile gets "
            "activated on multiple devices. So, the link-layer address of \"stable-ll\" and "
            "\"stable-llt\" will be a generated address derived from the stable id. The DUID-LLT "
            "time value in the \"stable-llt\" option will be picked among a static timespan of "
            "three years (the upper bound of the interval is the same constant timestamp used in "
            "\"llt\"). When the property is unset, the global value provided for "
            "\"ipv6.dhcp-duid\" is used. If no global value is provided, the default \"lease\" "
            "value is assumed."
        ),
    )
    dhcp_pd_hint: Optional[str] = Field(
        alias="dhcp-pd-hint",
        default=NM_SETTING_IP6CONFIG_DEFAULTS["dhcp-pd-hint"],
        description=(
            "A IPv6 address followed by a slash and a prefix length. If set, the value is sent to "
            "the DHCPv6 server as hint indicating the prefix delegation (IA_PD) we want to "
            "receive. To only hint a prefix length without prefix, set the address part to the "
            "zero address (for example \"::/60\")."
        ),
    )
    ip6_privacy: Optional[int] = Field(
        alias="ip6-privacy",
        default=NM_SETTING_IP6CONFIG_DEFAULTS["ip6-privacy"],
        description=(
            "Configure IPv6 Privacy Extensions for SLAAC, described in RFC4941. If enabled, it "
            "makes the kernel generate a temporary IPv6 address in addition to the public one "
            "generated from MAC address via modified EUI-64. This enhances privacy, but could "
            "cause problems in some applications, on the other hand. The permitted values are: -1: "
            "unknown, 0: disabled, 1: enabled (prefer public address), 2: enabled (prefer "
            "temporary addresses). Having a per-connection setting set to \"-1\" (default) means "
            "fallback to global configuration \"ipv6.ip6-privacy\". If it's also unspecified or "
            "set to \"-1\", fallback to read \"/proc/sys/net/ipv6/conf/default/use_tempaddr\". "
            "Note that this setting is distinct from the Stable Privacy addresses that can be "
            "enabled with the \"addr-gen-mode\" property's \"stable-privacy\" setting as another "
            "way of avoiding host tracking with IPv6 addresses."
        ),
    )
    mtu: Optional[int] = Field(
        default=NM_SETTING_IP6CONFIG_DEFAULTS["mtu"],
        description=(
            "Maximum transmission unit size, in bytes. If zero (the default), the MTU is set "
            "automatically from router advertisements or is left equal to the link-layer MTU. If "
            "greater than the link-layer MTU, or greater than zero but less than the minimum IPv6 "
            "MTU of 1280, this value has no effect."
        ),
    )
    ra_timeout: Optional[int] = Field(
        alias="ra-timeout",
        default=NM_SETTING_IP6CONFIG_DEFAULTS["ra-timeout"],
        description=(
            "A timeout for waiting Router Advertisements in seconds. If zero (the default), a "
            "globally configured default is used. If still unspecified, the timeout depends on the "
            "sysctl settings of the device. Set to 2147483647 (MAXINT32) for infinity."
        ),
    )
    temp_preferred_lifetime: Optional[int] = Field(
        alias="temp-preferred-lifetime",
        default=NM_SETTING_IP6CONFIG_DEFAULTS["temp-preferred-lifetime"],
        description=(
            "The preferred lifetime of autogenerated temporary addresses, in seconds. Having a "
            "per-connection setting set to \"0\" (default) means fallback to global configuration "
            "\"ipv6.temp-preferred-lifetime\" setting. If it's also unspecified or set to \"0\", "
            "fallback to read \"/proc/sys/net/ipv6/conf/default/temp_prefered_lft\"."
        ),
    )
    temp_valid_lifetime: Optional[int] = Field(
        alias="temp-valid-lifetime",
        default=NM_SETTING_IP6CONFIG_DEFAULTS["temp-valid-lifetime"],
        description=(
            "The valid lifetime of autogenerated temporary addresses, in seconds. Having a "
            "per-connection setting set to \"0\" (default) means fallback to global configuration "
            "\"ipv6.temp-valid-lifetime\" setting. If it's also unspecified or set to \"0\", "
            "fallback to read \"/proc/sys/net/ipv6/conf/default/temp_valid_lft\"."
        ),
    )
    token: Optional[str] = Field(
        default=NM_SETTING_IP6CONFIG_DEFAULTS["token"],
        description=(
            "Configure the token for draft-chown-6man-tokenised-ipv6-identifiers-02 IPv6 tokenized "
            "interface identifiers. Useful with eui64 addr-gen-mode. When set, the token is used "
            "as IPv6 interface identifier instead of the hardware address. This only applies to "
            "addresses from stateless autoconfiguration, not to IPv6 link local addresses."
        )
    )


class ConnectionSettingsWiredModel(BaseModel):
    """Model for the '802-3-ethernet' setting of a NetworkManager Connection"""

    accept_all_mac_addresses: Optional[int] = Field(
        alias="accept-all-mac-addresses",
        default=NM_SETTING_WIRED_DEFAULTS["accept-all-mac-addresses"],
        description=(
            "When TRUE, setup the interface to accept packets for all MAC addresses. This is "
            "enabling the kernel interface flag IFF_PROMISC. When FALSE, the interface will only "
            "accept the packets with the interface destination mac address or broadcast."
        ),
    )
    assigned_mac_address: Optional[str] = Field(
        alias="assigned-mac-address",
        default=NM_SETTING_WIRED_DEFAULTS["assigned-mac-address"],
        description=(
            "The new field for the cloned MAC address. It can be either a hardware address in "
            "ASCII representation, or one of the special values \"preserve\", \"permanent\", "
            "\"random\" or \"stable\". This field replaces the deprecated \"cloned-mac-address\" "
            "on D-Bus, which can only contain explicit hardware addresses. Note that this property "
            "only exists in D-Bus API. libnm and nmcli continue to call this property "
            "\"cloned-mac-address\"."
        ),
    )
    auto_negotiate: Optional[bool] = Field(
        alias="auto-negotiate",
        default=NM_SETTING_WIRED_DEFAULTS["auto-negotiate"],
        description=(
            "When TRUE, enforce auto-negotiation of speed and duplex mode. If \"speed\" and "
            "\"duplex\" properties are both specified, only that single mode will be advertised "
            "and accepted during the link auto-negotiation process: this works only for BASE-T "
            "802.3 specifications and is useful for enforcing gigabits modes, as in these cases "
            "link negotiation is mandatory. When FALSE, \"speed\" and \"duplex\" properties should "
            "be both set or link configuration will be skipped."
        ),
    )
    cloned_mac_address: Optional[str] = Field(
        alias="cloned-mac-address",
        default=None,
        description=(
            "This D-Bus field is deprecated in favor of \"assigned-mac-address\" which is more "
            "flexible and allows specifying special variants like \"random\". For libnm and nmcli, "
            "this field is called \"cloned-mac-address\"."
        ),
        deprecated=True,
    )
    duplex: Optional[str] = Field(
        default=NM_SETTING_WIRED_DEFAULTS["duplex"],
        description=(
            "When a value is set, either \"half\" or \"full\", configures the device to use the "
            "specified duplex mode. If \"auto-negotiate\" is \"yes\" the specified duplex mode "
            "will be the only one advertised during link negotiation: this works only for BASE-T "
            "802.3 specifications and is useful for enforcing gigabits modes, as in these cases "
            "link negotiation is mandatory. If the value is unset (the default), the link "
            "configuration will be either skipped (if \"auto-negotiate\" is \"no\", the default) "
            "or will be auto-negotiated (if \"auto-negotiate\" is \"yes\") and the local device "
            "will advertise all the supported duplex modes. Must be set together with the "
            "\"speed\" property if specified. Before specifying a duplex mode be sure your device "
            "supports it."
        ),
    )
    generate_mac_address_mask: Optional[str] = Field(
        alias="generate-mac-address-mask",
        default=NM_SETTING_WIRED_DEFAULTS["generate-mac-address-mask"],
        description=(
            "With \"cloned-mac-address\" setting \"random\" or \"stable\", by default all bits of "
            "the MAC address are scrambled and a locally-administered, unicast MAC address is "
            "created. This property allows to specify that certain bits are fixed. Note that the "
            "least significant bit of the first MAC address will always be unset to create a "
            "unicast MAC address. If the property is NULL, it is eligible to be overwritten by a "
            "default connection setting. If the value is still NULL or an empty string, the "
            "default is to create a locally-administered, unicast MAC address. If the value "
            "contains one MAC address, this address is used as mask. The set bits of the mask are "
            "to be filled with the current MAC address of the device, while the unset bits are "
            "subject to randomization. Setting \"FE:FF:FF:00:00:00\" means to preserve the OUI of "
            "the current MAC address and only randomize the lower 3 bytes using the \"random\" or "
            "\"stable\" algorithm. If the value contains one additional MAC address after the "
            "mask, this address is used instead of the current MAC address to fill the bits that "
            "shall not be randomized. For example, a value of "
            "\"FE:FF:FF:00:00:00 68:F7:28:00:00:00\" will set the OUI of the MAC address to "
            "68:F7:28, while the lower bits are randomized. A value of "
            "\"02:00:00:00:00:00 00:00:00:00:00:00\" will create a fully scrambled "
            "globally-administered, burned-in MAC address. If the value contains more than one "
            "additional MAC addresses, one of them is chosen randomly. For example, "
            "\"02:00:00:00:00:00 00:00:00:00:00:00 02:00:00:00:00:00\" will create a fully "
            "scrambled MAC address, randomly locally or globally administered."
        ),
    )
    mac_address: Optional[str] = Field(
        alias="mac-address",
        default=NM_SETTING_WIRED_DEFAULTS["mac-address"],
        description=(
            "If specified, this connection will only apply to the Ethernet device whose permanent "
            "MAC address matches. This property does not change the MAC address of the device "
            "(i.e. MAC spoofing)."
        ),
    )
    mac_address_blacklist: Optional[List[str]] = Field(
        alias="mac-address-blacklist",
        default=NM_SETTING_WIRED_DEFAULTS["mac-address-blacklist"],
        description=(
            "If specified, this connection will never apply to the Ethernet device whose permanent "
            "MAC address matches an address in the list. Each MAC address is in the standard "
            "hex-digits-and-colons notation (00:11:22:33:44:55)."
        ),
    )
    mac_address_denylist: Optional[List[str]] = Field(
        alias="mac-address-denylist",
        default=NM_SETTING_WIRED_DEFAULTS["mac-address-denylist"],
        description=(
            "If specified, this connection will never apply to the Ethernet device whose permanent "
            "MAC address matches an address in the list. Each MAC address is in the standard "
            "hex-digits-and-colons notation (00:11:22:33:44:55)."
        ),
    )
    mtu: Optional[int] = Field(
        default=NM_SETTING_WIRED_DEFAULTS["mtu"],
        description=(
            "If non-zero, only transmit packets of the specified size or smaller, breaking larger "
            "packets up into multiple Ethernet frames."
        ),
    )
    port: Optional[str] = Field(
        default=NM_SETTING_WIRED_DEFAULTS["port"],
        description=(
            "Specific port type to use if the device supports multiple attachment methods. One of "
            "\"tp\" (Twisted Pair), \"aui\" (Attachment Unit Interface), \"bnc\" (Thin Ethernet) "
            "or \"mii\" (Media Independent Interface). If the device supports only one port type, "
            "this setting is ignored."
        ),
    )
    s390_nettype: Optional[str] = Field(
        alias="s390-nettype",
        default=NM_SETTING_WIRED_DEFAULTS["s390-nettype"],
        description=(
            "s390 network device type; one of \"qeth\", \"lcs\", or \"ctc\", representing the "
            "different types of virtual network devices available on s390 systems."
        ),
    )
    s390_options: Optional[Dict[str, str]] = Field(
        alias="s390-options",
        default=NM_SETTING_WIRED_DEFAULTS["s390-options"],
        description=(
            "Dictionary of key/value pairs of s390-specific device options. Both keys and values "
            "must be strings. Allowed keys include \"portno\", \"layer2\", \"portname\", "
            "\"protocol\", among others. Key names must contain only alphanumeric characters (ie, "
            "[a-zA-Z0-9]). Currently, NetworkManager itself does nothing with this information. "
            "However, s390utils ships a udev rule which parses this information and applies it to "
            "the interface."
        ),
    )
    s390_subchannels: Optional[List[str]] = Field(
        alias="s390-subchannels",
        default=NM_SETTING_WIRED_DEFAULTS["s390-subchannels"],
        description=(
            "Identifies specific subchannels that this network device uses for communication with "
            "z/VM or s390 host. Like the \"mac-address\" property for non-z/VM devices, this "
            "property can be used to ensure this connection only applies to the network device "
            "that uses these subchannels. The list should contain exactly 3 strings, and each "
            "string may only be composed of hexadecimal characters and the period (.) character."
        ),
    )
    speed: Optional[int] = Field(
        default=NM_SETTING_WIRED_DEFAULTS["speed"],
        description=(
            "When a value greater than 0 is set, configures the device to use the specified speed. "
            "If \"auto-negotiate\" is \"yes\" the specified speed will be the only one advertised "
            "during link negotiation: this works only for BASE-T 802.3 specifications and is "
            "useful for enforcing gigabit speeds, as in this case link negotiation is mandatory. "
            "If the value is unset (0, the default), the link configuration will be either skipped "
            "(if \"auto-negotiate\" is \"no\", the default) or will be auto-negotiated (if "
            "\"auto-negotiate\" is \"yes\") and the local device will advertise all the supported "
            "speeds. In Mbit/s, ie 100 == 100Mbit/s. Must be set together with the \"duplex\" "
            "property when non-zero. Before specifying a speed value be sure your device supports "
            "it."
        ),
    )
    wake_on_lan: Optional[int] = Field(
        alias="wake-on-lan",
        default=NM_SETTING_WIRED_DEFAULTS["wake-on-lan"],
        description=(
            "The NMSettingWiredWakeOnLan options to enable. Not all devices support all options. "
            "May be any combination of 0x2 (phy), 0x4 (unicast), 0x8 (multicast), 0x10 "
            "(broadcast), 0x20 (arp), 0x40 (magic) or the special values 0x1 (default) (to use "
            "global settings) and 0x8000 (ignore) (to disable management of Wake-on-LAN in "
            "NetworkManager)."
        ),
    )
    wake_on_lan_password: Optional[str] = Field(
        alias="wake-on-lan-password",
        default=NM_SETTING_WIRED_DEFAULTS["wake-on-lan-password"],
        description=(
            "If specified, the password used with magic-packet-based Wake-on-LAN, represented as "
            "an Ethernet MAC address. If NULL, no password will be required."
        ),
    )


class ConnectionSettingsWirelessModel(BaseModel):
    """Model for the '802-11-wireless' setting of a NetworkManager Connection"""

    ap_isolation: Optional[int] = Field(
        alias="ap-isolation",
        default=NM_SETTING_WIRELESS_DEFAULTS["ap-isolation"],
        description=(
            "Configures AP isolation, which prevents communication between wireless devices "
            "connected to this AP. This property can be set to a value different from -1 (default) "
            "only when the interface is configured in AP mode. If set to 1 (true), devices are not "
            "able to communicate with each other. This increases security because it protects "
            "devices against attacks from other clients in the network. At the same time, it "
            "prevents devices to access resources on the same wireless networks as file shares, "
            "printers, etc. If set to 0 (false), devices can talk to each other. When set to -1 "
            "(default), the global default is used; in case the global default is unspecified it "
            "is assumed to be 0 (false)."
        ),
    )
    assigned_mac_address: Optional[str] = Field(
        alias="assigned-mac-address",
        default=NM_SETTING_WIRELESS_DEFAULTS["assigned-mac-address"],
        description=(
            "The new field for the cloned MAC address. It can be either a hardware address in "
            "ASCII representation, or one of the special values \"preserve\", \"permanent\", "
            "\"random\" or \"stable\". This field replaces the deprecated \"cloned-mac-address\" "
            "on D-Bus, which can only contain explicit hardware addresses. Note that this property "
            "only exists in D-Bus API. libnm and nmcli continue to call this property "
            "\"cloned-mac-address\"."
        ),
    )
    band: Optional[str] = Field(
        default=NM_SETTING_WIRELESS_DEFAULTS["band"],
        description=(
            "802.11 frequency band of the network. One of \"a\" for 5GHz 802.11a or \"bg\" for "
            "2.4GHz 802.11. This will lock associations to the Wi-Fi network to the specific band, "
            "i.e. if \"a\" is specified, the device will not associate with the same network in "
            "the 2.4GHz band even if the network's settings are compatible. This setting depends "
            "on specific driver capability and may not work with all drivers."
        ),
    )
    bssid: Optional[str] = Field(
        default=NM_SETTING_WIRELESS_DEFAULTS["bssid"],
        description=(
            "If specified, directs the device to only associate with the given access point. This "
            "capability is highly driver dependent and not supported by all devices. Note: this "
            "property does not control the BSSID used when creating an Ad-Hoc network and is "
            "unlikely to in the future. Locking a client profile to a certain BSSID will prevent "
            "roaming and also disable background scanning. That can be useful, if there is only "
            "one access point for the SSID."
        ),
    )
    channel: Optional[int] = Field(
        default=NM_SETTING_WIRELESS_DEFAULTS["channel"],
        description=(
            "Wireless channel to use for the Wi-Fi connection. The device will only join (or "
            "create for Ad-Hoc networks) a Wi-Fi network on the specified channel. Because channel "
            "numbers overlap between bands, this property also requires the \"band\" property to "
            "be set."
        ),
    )
    channel_width: Optional[int] = Field(
        alias="channel-width",
        default=NM_SETTING_WIRELESS_DEFAULTS["channel-width"],
        description=(
            "Specifies width of the wireless channel in Access Point (AP) mode. When set to 0 "
            "(auto) (the default), the channel width is automatically determined. At the moment, "
            "this means that the safest (smallest) width is chosen. If the value is not 0 (auto), "
            "then the 'channel' property must also be set. When using the 2.4GHz band, the width "
            "can be at most 40MHz. This property can be set to a value different from 0 (auto) "
            "only when the interface is configured in AP mode."
        ),
    )
    cloned_mac_address: Optional[str] = Field(
        alias="cloned-mac-address",
        default=NM_SETTING_WIRELESS_DEFAULTS["cloned-mac-address"],
        description=(
            "This D-Bus field is deprecated in favor of \"assigned-mac-address\" which is more "
            "flexible and allows specifying special variants like \"random\". For libnm and nmcli, "
            "this field is called \"cloned-mac-address\"."
        ),
        deprecated=True,
    )
    generate_mac_address_mask: Optional[str] = Field(
        alias="generate-mac-address-mask",
        default=NM_SETTING_WIRELESS_DEFAULTS["generate-mac-address-mask"],
        description=(
            "With \"cloned-mac-address\" setting \"random\" or \"stable\", by default all bits of "
            "the MAC address are scrambled and a locally-administered, unicast MAC address is "
            "created. This property allows to specify that certain bits are fixed. Note that the "
            "least significant bit of the first MAC address will always be unset to create a "
            "unicast MAC address. If the property is NULL, it is eligible to be overwritten by a "
            "default connection setting. If the value is still NULL or an empty string, the "
            "default is to create a locally-administered, unicast MAC address. If the value "
            "contains one MAC address, this address is used as mask. The set bits of the mask are "
            "to be filled with the current MAC address of the device, while the unset bits are "
            "subject to randomization. Setting \"FE:FF:FF:00:00:00\" means to preserve the OUI of "
            "the current MAC address and only randomize the lower 3 bytes using the \"random\" or "
            "\"stable\" algorithm. If the value contains one additional MAC address after the "
            "mask, this address is used instead of the current MAC address to fill the bits that "
            "shall not be randomized. For example, a value of "
            "\"FE:FF:FF:00:00:00 68:F7:28:00:00:00\" will set the OUI of the MAC address to "
            "68:F7:28, while the lower bits are randomized. A value of "
            "\"02:00:00:00:00:00 00:00:00:00:00:00\" will create a fully scrambled "
            "globally-administered, burned-in MAC address. If the value contains more than one "
            "additional MAC addresses, one of them is chosen randomly. For example, "
            "\"02:00:00:00:00:00 00:00:00:00:00:00 02:00:00:00:00:00\" will create a fully "
            "scrambled MAC address, randomly locally or globally administered."
        ),
    )
    hidden: Optional[bool] = Field(
        default=NM_SETTING_WIRELESS_DEFAULTS["hidden"],
        description=(
            "If TRUE, indicates that the network is a non-broadcasting network that hides its "
            "SSID. This works both in infrastructure and AP mode. In infrastructure mode, various "
            "workarounds are used for a more reliable discovery of hidden networks, such as "
            "probe-scanning the SSID. However, these workarounds expose inherent insecurities with "
            "hidden SSID networks, and thus hidden SSID networks should be used with caution. In "
            "AP mode, the created network does not broadcast its SSID. Note that marking the "
            "network as hidden may be a privacy issue for you (in infrastructure mode) or client "
            "stations (in AP mode), as the explicit probe-scans are distinctly recognizable on the "
            "air."
        ),
    )
    mac_address: Optional[str] = Field(
        alias="mac-address",
        default=None,
        description=(
            "If specified, this connection will only apply to the Wi-Fi device whose permanent MAC "
            "address matches. This property does not change the MAC address of the device (i.e. "
            "MAC spoofing)."
        ),
    )
    mac_address_blacklist: Optional[List[str]] = Field(
        alias="mac-address-blacklist",
        default=NM_SETTING_WIRELESS_DEFAULTS["mac-address-blacklist"],
        description=(
            "A list of permanent MAC addresses of Wi-Fi devices to which this connection should "
            "never apply. Each MAC address should be given in the standard hex-digits-and-colons "
            "notation (eg \"00:11:22:33:44:55\")."
        ),
    )
    mac_address_denylist: Optional[List[str]] = Field(
        alias="mac-address-denylist",
        default=NM_SETTING_WIRELESS_DEFAULTS["mac-address-denylist"],
        description=(
            "A list of permanent MAC addresses of Wi-Fi devices to which this connection should "
            "never apply. Each MAC address should be given in the standard hex-digits-and-colons "
            "notation (eg \"00:11:22:33:44:55\")."
        ),
    )
    mac_address_randomization: Optional[int] = Field(
        alias="mac-address-randomization",
        default=NM_SETTING_WIRELESS_DEFAULTS["mac-address-randomization"],
        description=(
            "One of 0 (default) (never randomize unless the user has set a global default to "
            "randomize and the supplicant supports randomization), 1 (never) (never randomize the "
            "MAC address), or 2 (always) (always randomize the MAC address). This property is "
            "deprecated since version 1.4. Use the \"cloned-mac-address\" property instead."
        ),
        deprecated=(
            "This property is deprecated since version 1.4. "
            "Use the \"cloned-mac-address\" property instead."
        ),
    )
    mode: Optional[str] = Field(
        default=NM_SETTING_WIRELESS_DEFAULTS["mode"],
        description=(
            "Wi-Fi network mode; one of \"infrastructure\", \"mesh\", \"adhoc\" or \"ap\". If "
            "blank, infrastructure is assumed."
        ),
    )
    mtu: Optional[int] = Field(
        default=NM_SETTING_WIRELESS_DEFAULTS["mtu"],
        description=(
            "If non-zero, only transmit packets of the specified size or smaller, breaking larger "
            "packets up into multiple Ethernet frames."
        ),
    )
    powersave: Optional[int] = Field(
        default=NM_SETTING_WIRELESS_DEFAULTS["powersave"],
        description=(
            "One of 2 (disable) (disable Wi-Fi power saving), 3 (enable) (enable Wi-Fi power "
            "saving), 1 (ignore) (don't touch currently configure setting) or 0 (default) (use the "
            "globally configured value). All other values are reserved."
        ),
    )
    rate: Optional[int] = Field(
        default=NM_SETTING_WIRELESS_DEFAULTS["rate"],
        description=(
            "This property is not implemented and has no effect. This property is deprecated since "
            "version 1.44. This property is not implemented and has no effect."
        ),
        deprecated=(
            "This property is deprecated since version 1.44. "
            "This property is not implemented and has no effect."
        ),
    )
    security: Optional[Any] = Field(
        default=NM_SETTING_WIRELESS_DEFAULTS["security"],
        description=(
            "This property is deprecated and has no effect. For backwards compatibility, it can be "
            "set to \"802-11-wireless-security\" if the profile has a wireless security setting."
        ),
        deprecated=(
            "This property is deprecated since version 1.4. "
            "Use the \"802-11-wireless-security\" property instead."
        ),
    )
    seen_bssids: Optional[List[str]] = Field(
        alias="seen-bssids",
        default=NM_SETTING_WIRELESS_DEFAULTS["seen-bssids"],
        description=(
            "A list of BSSIDs (each BSSID formatted as a MAC address like \"00:11:22:33:44:55\") "
            "that have been detected as part of the Wi-Fi network. NetworkManager internally "
            "tracks previously seen BSSIDs. The property is only meant for reading and reflects "
            "the BSSID list of NetworkManager. The changes you make to this property will not be "
            "preserved. This is not a regular property that the user would configure. Instead, "
            "NetworkManager automatically sets the seen BSSIDs and tracks them internally in "
            "\"/var/lib/NetworkManager/seen-bssids\" file."
        ),
    )
    ssid: str = Field(
        description=(
            "SSID of the Wi-Fi network. Must be specified."
        ),
    )
    tx_power: Optional[int] = Field(
        alias="tx-power",
        default=NM_SETTING_WIRELESS_DEFAULTS["tx-power"],
        description=(
            "This property is not implemented and has no effect. This property is deprecated since "
            "version 1.44. This property is not implemented and has no effect."
        ),
        deprecated=(
            "This property is deprecated since version 1.44. "
            "This property is not implemented and has no effect."
        ),
    )
    wake_on_wlan: Optional[int] = Field(
        alias="wake-on-wlan",
        default=NM_SETTING_WIRELESS_DEFAULTS["wake-on-wlan"],
        description=(
            "The NMSettingWirelessWakeOnWLan options to enable. Not all devices support all "
            "options. May be any combination of 0x2 (any), 0x4 (disconnect), 0x8 (magic), 0x10 "
            "(gtk-rekey-failure), 0x20 (eap-identity-request), 0x40 (4way-handshake), 0x80 "
            "(rfkill-release), 0x100 (tcp) or the special values 0x1 (default) (to use global "
            "settings) and 0x8000 (ignore) (to disable management of Wake-on-LAN in "
            "NetworkManager)."
        ),
    )


class ConnectionSettingsWirelessSecurityModel(BaseModel):
    """Model for the '802-11-wireless-security' setting of a NetworkManager Connection"""

    auth_alg: Optional[str] = Field(
        alias="auth-alg",
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["auth-alg"],
        description=(
            "When WEP is used (ie, key-mgmt = \"none\" or \"ieee8021x\") indicate the 802.11 "
            "authentication algorithm required by the AP here. One of \"open\" for Open System, "
            "\"shared\" for Shared Key, or \"leap\" for Cisco LEAP. When using Cisco LEAP (ie, "
            "key-mgmt = \"ieee8021x\" and auth-alg = \"leap\") the \"leap-username\" and "
            "\"leap-password\" properties must be specified."
        ),
    )
    fils: Optional[int] = Field(
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["fils"],
        description=(
            "Indicates whether Fast Initial Link Setup (802.11ai) must be enabled for the "
            "connection. One of 0 (default) (use global default value), 1 (disable) (disable "
            "FILS), 2 (optional) (enable FILS if the supplicant and the access point support it) "
            "or 3 (required) (enable FILS and fail if not supported). When set to 0 (default) and "
            "no global default is set, FILS will be optionally enabled."
        ),
    )
    group: Optional[List[str]] = Field(
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["group"],
        description=(
            "A list of group/broadcast encryption algorithms which prevents connections to Wi-Fi "
            "networks that do not utilize one of the algorithms in the list. For maximum "
            "compatibility leave this property empty. Each list element may be one of \"wep40\", "
            "\"wep104\", \"tkip\", or \"ccmp\"."
        ),
    )
    key_mgmt: str = Field(
        alias="key-mgmt",
        description=(
            "Key management used for the connection. One of \"none\" (WEP or no password "
            "protection), \"ieee8021x\" (Dynamic WEP), \"owe\" (Opportunistic Wireless "
            "Encryption), \"wpa-psk\" (WPA2 + WPA3 personal), \"sae\" (WPA3 personal only), "
            "\"wpa-eap\" (WPA2 + WPA3 enterprise) or \"wpa-eap-suite-b-192\" (WPA3 enterprise "
            "only). This property must be set for any Wi-Fi connection that uses security."
        ),
    )
    leap_password: Optional[str] = Field(
        alias="leap-password",
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["leap-password"],
        description=(
            "The login password for legacy LEAP connections (ie, key-mgmt = \"ieee8021x\" and "
            "auth-alg = \"leap\")."
        ),
    )
    leap_password_flags: Optional[int] = Field(
        alias="leap-password-flags",
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["leap-password-flags"],
        description=(
            "Flags indicating how to handle the \"leap-password\" property."
        ),
    )
    leap_username: Optional[str] = Field(
        alias="leap-username",
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["leap-username"],
        description=(
            "The login username for legacy LEAP connections (ie, key-mgmt = \"ieee8021x\" and "
            "auth-alg = \"leap\")."
        ),
    )
    pairwise: Optional[List[str]] = Field(
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["pairwise"],
        description=(
            "A list of pairwise encryption algorithms which prevents connections to Wi-Fi networks "
            "that do not utilize one of the algorithms in the list. For maximum compatibility "
            "leave this property empty. Each list element may be one of \"tkip\" or \"ccmp\"."
        ),
    )
    pmf: Optional[int] = Field(
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["pmf"],
        description=(
            "Indicates whether Protected Management Frames (802.11w) must be enabled for the "
            "connection. One of 0 (default) (use global default value), 1 (disable) (disable PMF), "
            "2 (optional) (enable PMF if the supplicant and the access point support it) or 3 "
            "(required) (enable PMF and fail if not supported). When set to 0 (default) and no "
            "global default is set, PMF will be optionally enabled."
        ),
    )
    proto: Optional[List[str]] = Field(
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["proto"],
        description=(
            "List of strings specifying the allowed WPA protocol versions to use. Each element may "
            "be one \"wpa\" (allow WPA) or \"rsn\" (allow WPA2/RSN). If not specified, both WPA "
            "and RSN connections are allowed."
        ),
    )
    psk: Optional[str] = Field(
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["psk"],
        description=(
            "Pre-Shared-Key for WPA networks. For WPA-PSK, it's either an ASCII passphrase of 8 to "
            "63 characters that is (as specified in the 802.11i standard) hashed to derive the "
            "actual key, or the key in form of 64 hexadecimal character. The WPA3-Personal "
            "networks use a passphrase of any length for SAE authentication."
        ),
    )
    psk_flags: Optional[int] = Field(
        alias="psk-flags",
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["psk-flags"],
        description=(
            "Flags indicating how to handle the \"psk\" property."
        ),
    )
    wep_key_flags: Optional[int] = Field(
        alias="wep-key-flags",
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["wep-key-flags"],
        description=(
            "Flags indicating how to handle the \"wep-key0\", \"wep-key1\", \"wep-key2\", and "
            "\"wep-key3\" properties."
        ),
    )
    wep_key_type: Optional[int] = Field(
        alias="wep-key-type",
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["wep-key-type"],
        description=(
            "Controls the interpretation of WEP keys. Allowed values are 1 (key), in which case "
            "the key is either a 10- or 26-character hexadecimal string, or a 5- or 13-character "
            "ASCII password; or 2 (passphrase), in which case the passphrase is provided as a "
            "string and will be hashed using the de-facto MD5 method to derive the actual WEP key."
        ),
    )
    wep_key0: Optional[str] = Field(
        alias="wep-key0",
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["wep-key0"],
        description=(
            "Index 0 WEP key. This is the WEP key used in most networks. See the \"wep-key-type\" "
            "property for a description of how this key is interpreted."
        ),
    )
    wep_key1: Optional[str] = Field(
        alias="wep-key1",
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["wep-key1"],
        description=(
            "Index 1 WEP key. This is the WEP key used in most networks. See the \"wep-key-type\" "
            "property for a description of how this key is interpreted."
        ),
    )
    wep_key2: Optional[str] = Field(
        alias="wep-key2",
        default=None,
        description=(
            "Index 2 WEP key. This is the WEP key used in most networks. See the \"wep-key-type\" "
            "property for a description of how this key is interpreted."
        ),
    )
    wep_key3: Optional[str] = Field(
        alias="wep-key3",
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["wep-key3"],
        description=(
            "Index 3 WEP key. This is the WEP key used in most networks. See the \"wep-key-type\" "
            "property for a description of how this key is interpreted."
        ),
    )
    wep_tx_keyidx: Optional[int] = Field(
        alias="wep-tx-keyidx",
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["wep-tx-keyidx"],
        description=(
            "When static WEP is used (ie, key-mgmt = \"none\") and a non-default WEP key index is "
            "used by the AP, put that WEP key index here. Valid values are 0 (default key) through "
            "3. Note that some consumer access points (like the Linksys WRT54G) number the keys "
            "1 - 4."
        ),
    )
    wps_method: Optional[int] = Field(
        alias="wps-method",
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["wps-method"],
        description=(
            "Flags indicating which mode of WPS is to be used if any. There's little point in "
            "changing the default setting as NetworkManager will automatically determine whether "
            "it's feasible to start WPS enrollment from the Access Point capabilities. WPS can be "
            "disabled by setting this property to a value of 1."
        ),
    )


class ConnectionProfile(BaseModel):
    """Model for a connection profile"""

    connection: ConnectionSettingsConnectionModel
    enterprise_auth: Optional[ConnectionSettings8021xModel] = Field(
        alias="802-1x", default=None
    )
    gsm: Optional[ConnectionSettingsGsmModel] = None
    ipv4: Optional[ConnectionSettingsIP4ConfigModel] = None
    ipv6: Optional[ConnectionSettingsIP6ConfigModel] = None
    wired: Optional[ConnectionSettingsWiredModel] = Field(
        alias="802-3-ethernet", default=None
    )
    wireless: Optional[ConnectionSettingsWirelessModel] = Field(
        alias="802-11-wireless", default=None
    )
    wireless_security: Optional[ConnectionSettingsWirelessSecurityModel] = Field(
        alias="802-11-wireless-security", default=None
    )
    activated: Optional[bool] = None


class ConnectionProfileLegacy(DefaultResponseModelLegacy):
    """Model for a connection profile (legacy)"""

    connection: Optional[ConnectionProfile] = None


class ConnectionProfiles(RootModel):
    """Model for response to request for all connection profiles"""

    root: List[ConnectionProfileInfo]


class ConnectionProfilesLegacy(DefaultResponseModelLegacy):
    """Model for response to request for all connection profiles (legacy)"""

    count: int
    connections: Dict[str, ConnectionProfileInfoLegacy]


class ConnectionProfileExportRequestModel(BaseModel):
    """Model for a request to export the connection profiles"""

    password: str


class ConnectionProfileImportRequestFormModel(BaseModel):
    """Model for a request to import the connection profiles"""

    password: str
    overwrite_existing: bool
    archive: BaseFile


class NetworkInterfacesResponseModel(RootModel):
    """Model for response to request for all network interfaces"""

    root: List[str]


class NetworkInterfacesResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for response to request for all network interfaces (legacy)"""

    interfaces: List[str]


class NetworkInterfaceStatus(BaseModel):
    """Model for a network interface status"""

    state: Optional[int] = None
    stateText: Optional[str] = None
    mtu: Optional[int] = None
    deviceType: Optional[int] = None
    deviceTypeText: Optional[str] = None


class NetworkInterfaceStatusLegacy(BaseModel):
    """Model for a network interface status (legacy)"""

    State: Optional[int] = None
    StateText: Optional[str] = None
    Mtu: Optional[int] = None
    DeviceType: Optional[int] = None
    DeviceTypeText: Optional[str] = None


class NetworkInterfaceWirelessProperties(BaseModel):
    """Model for wireless properties of a network interface"""

    bitrate: int
    permHwAddress: str
    mode: int
    regDomain: str
    hwAddress: str
    lastScan: int


class NetworkInterfaceWirelessPropertiesLegacy(BaseModel):
    """Model for wireless properties of a network interface (legacy)"""

    Bitrate: int
    PermHwAddress: str
    Mode: int
    RegDomain: str
    HwAddress: str
    LastScan: int


class NetworkInterfaceWiredProperties(BaseModel):
    """Model for wired properties of a network interface"""

    permHwAddress: str
    speed: int
    carrier: bool
    hwAddress: str


class NetworkInterfaceWiredPropertiesLegacy(BaseModel):
    """Model for wired properties of a network interface (legacy)"""

    PermHwAddress: str
    Speed: int
    Carrier: bool
    HwAddress: str


class AddressDataModel(BaseModel):
    """Model for an address data"""

    address: str
    prefix: int


class RouteDataModel(BaseModel):
    """Model for a route data"""

    dest: str
    prefix: int
    metric: str
    nextHop: str


class RouteDataModelLegacy(BaseModel):
    """Model for a route data (legacy)"""

    dest: str
    prefix: int
    metric: str
    next_hop: str


class IP4ConfigModel(BaseModel):
    """Model for the IPv4 configuration"""

    addressData: Optional[List[AddressDataModel]] = None
    routeData: Optional[List[RouteDataModel]] = None
    gateway: Optional[str] = None
    domains: Optional[List[str]] = None
    nameservers: Optional[List[str]] = None
    winsServers: Optional[List[str]] = None


class IP4ConfigModelLegacy(BaseModel):
    """Model for the IPv4 configuration (legacy)"""

    Addresses: Optional[Dict[str, str]] = None
    AddressData: Optional[List[AddressDataModel]] = None
    Routes: Optional[Dict[str, str]] = None
    RouteData: Optional[List[RouteDataModelLegacy]] = None
    Gateway: Optional[str] = None
    Domains: Optional[List[str]] = None
    NameserverData: Optional[List[str]] = None
    WinsServerData: Optional[List[str]] = None


class IP6ConfigModel(BaseModel):
    """Model for the IPv6 configuration"""

    addressData: Optional[List[AddressDataModel]] = None
    routeData: Optional[List[RouteDataModel]] = None
    gateway: Optional[str] = None
    domains: Optional[List[str]] = None
    nameservers: Optional[List[str]] = None


class IP6ConfigModelLegacy(BaseModel):
    """Model for the IPv6 configuration (legacy)"""

    Addresses: Optional[Dict[str, str]] = None
    AddressData: Optional[List[AddressDataModel]] = None
    Routes: Optional[Dict[str, str]] = None
    RouteData: Optional[List[RouteDataModelLegacy]] = None
    Gateway: Optional[str] = None
    Domains: Optional[List[str]] = None
    NameserverData: Optional[List[str]] = None
    WinsServerData: Optional[List[str]] = None


class DhcpConfigModel(BaseModel):
    """Model for the DHCP configuration"""

    options: Optional[Dict[str, str]] = None


class DhcpConfigModelLegacy(BaseModel):
    """Model for the DHCP configuration (legacy)"""

    Options: Optional[Dict[str, str]] = None


class AvailableApChannel(BaseModel):
    """A WLAN channel available for use in access point (AP) mode"""

    frequency: int
    channel: int


class NetworkInterfaceAvailableApChannelsResponseModel(RootModel):
    """List of available AP channels"""

    root: List[AvailableApChannel]


class NetworkInterfaceAvailableApChannelsResponseModelLegacy(
    DefaultResponseModelLegacy
):
    """List of available AP channels (legacy)"""

    channels: List[AvailableApChannel]


class IPv4DhcpLease(BaseModel):
    """Model for an IPv4 DHCP lease"""

    expiry: int = Field(
        description=(
            "The expiration time (seconds since unix epoch), "
            "0 means infinite (static lease)"
        )
    )
    macAddress: str = Field(
        description=(
            "The link address, in format XX-YY:YY:YY[...], where XX is the ARP hardware type. "
            '"XX-" may be omitted for Ethernet'
        )
    )
    ipAddress: str = Field(description="The IPv4 address of the client")
    hostname: str = Field(description='The hostname of the client or "*" for none')
    clientIdentifier: str = Field(
        description="The client identifier (colon-separated hex bytes) or '*' for none"
    )


class IPv6DhcpLease(BaseModel):
    """Model for an IPv6 DHCP lease"""

    expiry: int = Field(
        description=(
            "The expiration time (seconds since unix epoch), "
            "0 means infinite (static lease)"
        )
    )
    iaid: str = Field(
        description=(
            "The IAID as a Big Endian decimal number, "
            "prefixed by T for IA_TAs (temporary addresses)"
        )
    )
    ipAddress: str = Field(description="The IPv6 address of the client")
    hostname: str = Field(description='The hostname of the client or "*" for none')
    clientDuid: str = Field(
        description="The client DUID (colon-separated hex bytes) or '*' if unknown"
    )


class NetworkInterfaceDhcpLeasesResponseModel(BaseModel):
    """List of current DHCP leases"""

    ipv4: list[IPv4DhcpLease]
    ipv6: list[IPv6DhcpLease]


class NetworkInterfaceDhcpLeasesResponseModelLegacy(DefaultResponseModelLegacy):
    """List of current DHCP leases (legacy)"""

    leases: NetworkInterfaceDhcpLeasesResponseModel


class NetworkInterfaceSummitStatusResponseModel(BaseModel):
    """Summit status model"""

    last: Optional[str] = None
    best: Optional[str] = None


class NetworkInterfaceSummitStatusResponseModelLegacy(DefaultResponseModelLegacy):
    """Summit status model (legacy)"""

    last: Optional[str] = None
    best: Optional[str] = None


class NetworkInterfaceResponseModel(BaseModel):
    """Model for response to request for a specific network interface"""

    status: Optional[NetworkInterfaceStatus] = None
    ip4Config: Optional[IP4ConfigModel] = None
    ip6Config: Optional[IP6ConfigModel] = None
    dhcp4Config: Optional[DhcpConfigModel] = None
    dhcp6Config: Optional[DhcpConfigModel] = None
    wireless: Optional[NetworkInterfaceWirelessProperties] = None
    activeAccessPoint: Optional[ActiveAccessPoint] = None
    wired: Optional[NetworkInterfaceWiredProperties] = None
    udi: Optional[str] = None
    path: Optional[str] = None
    interface: Optional[str] = None
    ipInterface: Optional[str] = None
    driver: Optional[str] = None
    driverVersion: Optional[str] = None
    firmwareVersion: Optional[str] = None
    capabilities: Optional[int] = None
    stateReason: Optional[int] = None
    activeConnection: Optional[ConnectionSettingsConnectionModel] = None
    managed: Optional[bool] = Field(default=False)
    autoconnect: Optional[bool] = None
    firmwareMissing: Optional[bool] = Field(default=False)
    nmPluginMissing: Optional[bool] = Field(default=False)
    availableConnections: Optional[List[ConnectionSettingsConnectionModel]] = None
    physicalPortId: Optional[str] = None
    metered: Optional[int] = None
    meteredText: Optional[str] = None
    lldpNeighbors: Optional[List[str]] = None
    real: Optional[bool] = None
    ip4Connectivity: Optional[int] = None
    ip4ConnectivityText: Optional[str] = None
    ip6Connectivity: Optional[int] = None
    ip6ConnectivityText: Optional[str] = None
    interfaceFlags: Optional[int] = None


class NetworkInterfaceStatusModelLegacy(BaseModel):
    """Model for a network interface status (legacy)"""

    status: Optional[NetworkInterfaceStatusLegacy] = None
    ip4config: Optional[IP4ConfigModelLegacy] = None
    ip6config: Optional[IP6ConfigModelLegacy] = None
    dhcp4config: Optional[DhcpConfigModelLegacy] = None
    dhcp6config: Optional[DhcpConfigModelLegacy] = None
    wireless: Optional[NetworkInterfaceWirelessPropertiesLegacy] = None
    activeaccesspoint: Optional[ActiveAccessPointLegacy] = None
    wired: Optional[NetworkInterfaceWiredPropertiesLegacy] = None
    udi: Optional[str] = None
    path: Optional[str] = None
    interface: Optional[str] = None
    ip_interface: Optional[str] = None
    driver: Optional[str] = None
    driver_version: Optional[str] = None
    firmware_version: Optional[str] = None
    capabilities: Optional[int] = None
    state_reason: Optional[int] = None
    connection_active: Optional[ConnectionSettingsConnectionModel] = None
    managed: Optional[bool] = Field(default=False)
    autoconnect: Optional[bool] = None
    firmware_missing: Optional[bool] = Field(default=False)
    nm_plugin_missing: Optional[bool] = Field(default=False)
    available_connections: Optional[List[ConnectionSettingsConnectionModel]] = None
    physical_port_id: Optional[str] = None
    metered: Optional[int] = None
    metered_text: Optional[str] = None
    lldp_neighbors: Optional[List[str]] = None
    real: Optional[bool] = None
    ip4connectivity: Optional[int] = None
    ip4connectivity_text: Optional[str] = None
    ip6connectivity: Optional[int] = None
    ip6connectivity_text: Optional[str] = None
    interface_flags: Optional[int] = None


class NetworkInterfaceResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for response to request for a specific network interface (legacy)"""

    properties: Optional[NetworkInterfaceStatusModelLegacy] = None


class NetworkInterfaceStatsResponseModel(BaseModel):
    """Model for response to request for network interface stats"""

    rxBytes: int
    rxPackets: int
    rxErrors: int
    rxDropped: int
    multicast: int
    txBytes: int
    txPackets: int
    txErrors: int
    txDropped: int


class NetworkInterfaceStatsModelLegacy(BaseModel):
    """Model for network interface stats (legacy)"""

    rx_bytes: int
    rx_packets: int
    rx_errors: int
    rx_dropped: int
    multicast: int
    tx_bytes: int
    tx_packets: int
    tx_errors: int
    tx_dropped: int


class NetworkInterfaceStatsResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for response to request for network interface stats (legacy)"""

    statistics: NetworkInterfaceStatsModelLegacy


class NetworkInterfaceDriverInfoResponseModel(BaseModel):
    """Model for response to request for network interface driver info"""

    adoptedCountryCode: str
    otpCountryCode: str


class NetworkInterfaceDriverInfoResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for response to request for network interface driver info (legacy)"""

    driverInfo: NetworkInterfaceDriverInfoResponseModel


class StationRateInfo(BaseModel):
    """Station dump rate information"""

    rate: int | None = Field(description="The rate in kbps")
    channelWidth: int | None = Field(description="The channel width in MHz")


class Station(BaseModel):
    """Station dump information"""

    signal: int | None = Field(description="The signal strength in dBm")
    inactive: int | None = Field(
        description="The time in milliseconds since the station was last active"
    )
    connectedTime: int | None = Field(
        description="The time in seconds that the station has been connected"
    )
    rxPackets: int | None = Field(description="The number of received packets")
    txPackets: int | None = Field(description="The number of transmitted packets")
    beaconRx: int | None = Field(
        description="The number of beacons received from this peer"
    )
    rxRate: StationRateInfo | None
    txRate: StationRateInfo | None
    rxBytes: int | None = Field(description="The number of received bytes")
    txBytes: int | None = Field(description="The number of transmitted bytes")
    rxDuration: int | None = Field(
        description=(
            "Aggregate PPDU duration for all frames received from the station in "
            "microseconds"
        )
    )
    txRetries: int | None = Field(
        description="The number of transmitted packets that required retries"
    )
    txFailed: int | None = Field(
        description="The number of transmitted packets that failed"
    )
    beaconLoss: int | None = Field(
        description="The count of times beacon loss was detected"
    )
    rxDropMisc: int | None = Field(
        description="The number of received packets dropped for unspecified reasons"
    )
    dtimPeriod: int | None = Field(
        description="The Delivery Traffic Indication Message (DTIM) period for beaconing"
    )
    beaconInterval: int | None = Field(
        description="The beacon interval in milliseconds"
    )


class NetworkInterfaceStationDumpResponseModel(RootModel):
    """Dictionary of station dump information indexed by MAC address"""

    root: Dict[str, Station]


class NetworkInterfaceStationDumpResponseModelLegacy(DefaultResponseModelLegacy):
    """Dictionary of station dump information indexed by MAC address (legacy)"""

    stations: NetworkInterfaceStationDumpResponseModel


class AddNetworkInterfaceRequestModelLegacy(BaseModel):
    """Model for a request to add a network interface (legacy)"""

    interface: str = Field(default="wlan1")
    type: str = Field(default="STA")


class RemoveNetworkInterfaceRequestModelLegacy(BaseModel):
    """Model for a request to remove a network interface (legacy)"""

    interface: str = Field(default="wlan1")


class NetworkInterfaceInfoRequestModelLegacy(BaseModel):
    """Model for a request to remove a network interface (legacy)"""

    name: str = Field(default="wlan0")


class WiFiEnableInfoResponseModel(DefaultResponseModelLegacy):
    """Model for response to request for Wi-Fi enable state"""

    wifiRadioSoftwareEnabled: bool
    wifiRadioHardwareEnabled: bool


class WiFiEnableInfoResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for response to request for Wi-Fi enable state (legacy)"""

    wifi_radio_software_enabled: bool
    wifi_radio_hardware_enabled: bool


class WiFiEnableRequestQueryLegacy(BaseModel):
    """Model for a request to enable/disable Wi-Fi (legacy)"""

    enable: str = Field(default="true")


class WiFiEnableRequestResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for response to enable/disable Wi-Fi (legacy)"""

    wifi_radio_software_enabled: bool


class NetworkStatusResponseModel(BaseModel):
    """Model for response to request for network status"""

    status: Optional[Dict[str, NetworkInterfaceResponseModel]] = None
    devices: Optional[int] = None


class NetworkStatusResponseModelLegacy(BaseModel):
    """Model for response to request for network status (legacy)"""

    status: Optional[Dict[str, NetworkInterfaceResponseModelLegacy]] = None
    devices: Optional[int] = None


class DefinitionsModel(BaseModel):
    """Model for definitions"""

    SDCERR: Dict[str, int]
    PERMISSIONS: Dict[str, Any]
    DEVICE_TYPES: Dict[str, str]
    DEVICE_STATES: Dict[str, str]
    PLUGINS: List[str]
    SETTINGS: Dict[str, Any]


class DefinitionsResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for response to request for definitions (legacy)"""

    Definitions: Optional[DefinitionsModel] = None
