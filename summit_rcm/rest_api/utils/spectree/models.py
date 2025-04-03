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
    NMSettingSecretFlags,
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
        alias="auth-retries", default=NM_SETTING_CONNECTION_DEFAULTS["auth-retries"]
    )
    autoconnect: Optional[bool] = Field(
        default=NM_SETTING_CONNECTION_DEFAULTS["autoconnect"]
    )
    autoconnect_priority: Optional[int] = Field(
        alias="autoconnect-priority",
        default=NM_SETTING_CONNECTION_DEFAULTS["autoconnect-priority"],
    )
    autoconnect_retries: Optional[int] = Field(
        alias="autoconnect-retries",
        default=NM_SETTING_CONNECTION_DEFAULTS["autoconnect-retries"],
    )
    autoconnect_slaves: Optional[int] = Field(
        alias="autoconnect-slaves",
        default=NM_SETTING_CONNECTION_DEFAULTS["autoconnect-slaves"],
    )
    dns_over_tls: Optional[int] = Field(
        alias="dns-over-tls", default=NM_SETTING_CONNECTION_DEFAULTS["dns-over-tls"]
    )
    gateway_ping_timeout: Optional[int] = Field(
        alias="gateway-ping-timeout",
        default=NM_SETTING_CONNECTION_DEFAULTS["gateway-ping-timeout"],
    )
    id: Optional[str] = None
    interface_name: Optional[str] = Field(alias="interface-name", default=None)
    lldp: Optional[int] = Field(default=NM_SETTING_CONNECTION_DEFAULTS["lldp"])
    llmnr: Optional[int] = Field(default=NM_SETTING_CONNECTION_DEFAULTS["llmnr"])
    master: Optional[str] = None
    mdns: Optional[int] = Field(default=NM_SETTING_CONNECTION_DEFAULTS["mdns"])
    metered: Optional[int] = Field(default=NM_SETTING_CONNECTION_DEFAULTS["metered"])
    mptcp_flags: Optional[int] = Field(
        alias="mptcp-flags", default=NM_SETTING_CONNECTION_DEFAULTS["mptcp-flags"]
    )
    mud_url: Optional[str] = Field(default=NM_SETTING_CONNECTION_DEFAULTS["mud-url"])
    multi_connect: Optional[int] = Field(
        alias="multi-connect", default=NM_SETTING_CONNECTION_DEFAULTS["multi-connect"]
    )
    permissions: Optional[List[str]] = Field(
        default=NM_SETTING_CONNECTION_DEFAULTS["permissions"]
    )
    read_only: Optional[bool] = Field(
        alias="read-only", default=NM_SETTING_CONNECTION_DEFAULTS["read-only"]
    )
    secondaries: Optional[List[str]] = Field(
        default=NM_SETTING_CONNECTION_DEFAULTS["secondaries"]
    )
    slave_type: Optional[str] = Field(alias="slave-type", default=None)
    stable_id: Optional[str] = Field(alias="stable-id", default=None)
    timestamp: Optional[int] = Field(
        default=NM_SETTING_CONNECTION_DEFAULTS["timestamp"]
    )
    type: Optional[str] = None
    uuid: Optional[str] = None
    wait_activation_delay: Optional[int] = Field(
        alias="wait-activation-delay",
        default=NM_SETTING_CONNECTION_DEFAULTS["wait-activation-delay"],
    )
    wait_device_timeout: Optional[int] = Field(
        alias="wait-device-timeout",
        default=NM_SETTING_CONNECTION_DEFAULTS["wait-device-timeout"],
    )
    zone: Optional[str] = None


class ConnectionSettings8021xModel(BaseModel):
    """Model for the '802-1x' setting of a NetworkManager Connection"""

    altsubject_matches: Optional[List[str]] = Field(
        alias="altsubject-matches",
        default=NM_SETTING_8021X_DEFAULTS["altsubject-matches"],
    )
    anonymous_identity: Optional[str] = Field(alias="anonymous-identity", default=None)
    auth_timeout: Optional[int] = Field(
        alias="auth-timeout", default=NM_SETTING_8021X_DEFAULTS["auth-timeout"]
    )
    ca_cert: Optional[str] = Field(alias="ca-cert", default=None)
    ca_cert_password: Optional[str] = Field(alias="ca-cert-password", default=None)
    ca_cert_password_flags: Optional[int] = Field(
        alias="ca-cert-password-flags",
        default=NM_SETTING_8021X_DEFAULTS["ca-cert-password-flags"],
    )
    ca_path: Optional[str] = Field(alias="ca-path", default=None)
    client_cert: Optional[str] = Field(alias="client-cert", default=None)
    client_cert_password: Optional[str] = Field(
        alias="client-cert-password", default=None
    )
    client_cert_password_flags: Optional[int] = Field(
        alias="client-cert-password-flags",
        default=NM_SETTING_8021X_DEFAULTS["client-cert-password-flags"],
    )
    domain_match: Optional[str] = Field(alias="domain-match", default=None)
    domain_suffix_match: Optional[str] = Field(
        alias="domain-suffix-match", default=None
    )
    eap: Optional[List[str]] = Field(default=NM_SETTING_8021X_DEFAULTS["eap"])
    identity: Optional[str] = None
    optional: Optional[bool] = Field(default=NM_SETTING_8021X_DEFAULTS["optional"])
    pac_file: Optional[str] = Field(alias="pac-file", default=None)
    password: Optional[str] = None
    password_flags: Optional[int] = Field(
        default=NM_SETTING_8021X_DEFAULTS["password-flags"]
    )
    password_raw: Optional[str] = Field(alias="password-raw", default=None)
    password_raw_flags: Optional[int] = Field(
        alias="password-raw-flags",
        default=NM_SETTING_8021X_DEFAULTS["password-raw-flags"],
    )
    phase1_auth_flags: Optional[int] = Field(
        alias="phase1-auth-flags",
        default=NM_SETTING_8021X_DEFAULTS["phase1-auth-flags"],
    )
    phase1_fast_provisioning: Optional[str] = Field(
        alias="phase1-fast-provisioning", default=None
    )
    phase1_peaplabel: Optional[str] = Field(alias="phase1-peaplabel", default=None)
    phase1_peapver: Optional[str] = Field(alias="phase1-peapver", default=None)
    phase2_altsubject_matches: Optional[List[str]] = Field(
        alias="phase2-altsubject-matches",
        default=NM_SETTING_8021X_DEFAULTS["phase2-altsubject-matches"],
    )
    phase2_auth: Optional[str] = Field(alias="phase2-auth", default=None)
    phase2_autheap: Optional[str] = Field(alias="phase2-autheap", default=None)
    phase2_ca_cert: Optional[str] = Field(alias="phase2-ca-cert", default=None)
    phase2_ca_cert_password: Optional[str] = Field(
        alias="phase2-ca-cert-password", default=None
    )
    phase2_ca_cert_password_flags: Optional[int] = Field(
        alias="phase2-ca-cert-password-flags",
        default=NM_SETTING_8021X_DEFAULTS["phase2-ca-cert-password-flags"],
    )
    phase2_ca_path: Optional[str] = Field(alias="phase2-ca-path", default=None)
    phase2_client_cert: Optional[str] = Field(alias="phase2-client-cert", default=None)
    phase2_client_cert_password: Optional[str] = Field(
        alias="phase2-client-cert-password", default=None
    )
    phase2_client_cert_password_flags: Optional[int] = Field(
        alias="phase2-client-cert-password-flags",
        default=NM_SETTING_8021X_DEFAULTS["phase2-client-cert-password-flags"],
    )
    phase2_domain_match: Optional[str] = Field(
        alias="phase2-domain-match", default=None
    )
    phase2_domain_suffix_match: Optional[str] = Field(
        alias="phase2-domain-suffix-match", default=None
    )
    phase2_private_key: Optional[str] = Field(alias="phase2-private-key", default=None)
    phase2_private_key_password: Optional[str] = Field(
        alias="phase2-private-key-password",
        default=None,
    )
    phase2_private_key_password_flags: Optional[int] = Field(
        alias="phase2-private-key-password-flags",
        default=NM_SETTING_8021X_DEFAULTS["phase2-private-key-password-flags"],
    )
    phase2_subject_match: Optional[str] = Field(
        alias="phase2-subject-match", default=None
    )
    pin: Optional[str] = None
    pin_flags: Optional[int] = Field(
        alias="pin-flags", default=NM_SETTING_8021X_DEFAULTS["pin-flags"]
    )
    private_key: Optional[str] = Field(alias="private-key", default=None)
    private_key_password: Optional[str] = Field(
        alias="private-key-password", default=None
    )
    private_key_password_flags: Optional[int] = Field(
        alias="private-key-password-flags",
        default=NM_SETTING_8021X_DEFAULTS["private-key-password-flags"],
    )
    subject_match: Optional[str] = Field(alias="subject-match", default=None)
    system_ca_certs: Optional[bool] = Field(
        alias="system-ca-certs", default=NM_SETTING_8021X_DEFAULTS["system-ca-certs"]
    )


class ConnectionSettingsGsmModel(BaseModel):
    """Model for the 'gsm' setting of a NetworkManager Connection"""

    apn: Optional[str] = None
    auto_config: Optional[bool] = Field(alias="auto-config", default=False)
    device_id: Optional[str] = Field(alias="device-id", default=None)
    home_only: Optional[bool] = Field(alias="home-only", default=False)
    mtu: Optional[int] = Field(default=0)
    network_id: Optional[str] = Field(alias="network-id", default=None)
    number: Optional[str] = None
    password: Optional[str] = None
    password_flags: Optional[int] = Field(
        alias="password-flags", default=NMSettingSecretFlags.NM_SETTING_SECRET_FLAG_NONE
    )
    pin: Optional[str] = None
    pin_flags: Optional[int] = Field(
        alias="pin-flags", default=NMSettingSecretFlags.NM_SETTING_SECRET_FLAG_NONE
    )
    sim_id: Optional[str] = Field(alias="sim-id", default=None)
    sim_operator_id: Optional[str] = Field(alias="sim-operator-id", default=None)
    username: Optional[str] = None


class ConnectionSettingsIPConfigModel(BaseModel):
    """Base model for an IP config setting of a NetworkManager Connection"""

    addresses: Optional[List[str]] = None
    auto_route_ext_gw: Optional[bool] = Field(
        alias="auto-route-ext-gw",
        default=NM_SETTING_IPCONFIG_DEFAULTS["auto-route-ext-gw"],
    )
    dad_timeout: Optional[int] = Field(
        alias="dad-timeout", default=NM_SETTING_IPCONFIG_DEFAULTS["dad-timeout"]
    )
    dhcp_hostname: Optional[str] = Field(alias="dhcp-hostname", default=None)
    dhcp_hostname_flags: Optional[int] = Field(
        alias="dhcp-hostname-flags",
        default=NM_SETTING_IPCONFIG_DEFAULTS["dhcp-hostname-flags"],
    )
    dhcp_iaid: Optional[str] = Field(alias="dhcp-iaid", default=None)
    dhcp_reject_servers: Optional[List[str]] = Field(
        alias="dhcp-reject-servers",
        default=NM_SETTING_IPCONFIG_DEFAULTS["dhcp-reject-servers"],
    )
    dhcp_send_hostname: Optional[bool] = Field(
        alias="dhcp-send-hostname",
        default=NM_SETTING_IPCONFIG_DEFAULTS["dhcp-send-hostname"],
    )
    dhcp_timeout: Optional[int] = Field(
        alias="dhcp-timeout", default=NM_SETTING_IPCONFIG_DEFAULTS["dhcp-timeout"]
    )
    dns: Optional[List[str]] = Field(default=NM_SETTING_IPCONFIG_DEFAULTS["dns"])
    dns_options: Optional[List[str]] = Field(
        alias="dns-options", default=NM_SETTING_IPCONFIG_DEFAULTS["dns-options"]
    )
    dns_priority: Optional[int] = Field(
        alias="dns-priority", default=NM_SETTING_IPCONFIG_DEFAULTS["dns-priority"]
    )
    dns_search: Optional[List[str]] = Field(
        alias="dns-search", default=NM_SETTING_IPCONFIG_DEFAULTS["dns-search"]
    )
    gateway: Optional[str] = None
    ignore_auto_dns: Optional[bool] = Field(
        alias="ignore-auto-dns", default=NM_SETTING_IPCONFIG_DEFAULTS["ignore-auto-dns"]
    )
    ignore_auto_routes: Optional[bool] = Field(
        alias="ignore-auto-routes",
        default=NM_SETTING_IPCONFIG_DEFAULTS["ignore-auto-routes"],
    )
    may_fail: Optional[bool] = Field(
        alias="may-fail", default=NM_SETTING_IPCONFIG_DEFAULTS["may-fail"]
    )
    method: Optional[str] = None
    never_default: Optional[bool] = Field(
        alias="never-default", default=NM_SETTING_IPCONFIG_DEFAULTS["never-default"]
    )
    required_timeout: Optional[int] = Field(
        alias="required-timeout",
        default=NM_SETTING_IPCONFIG_DEFAULTS["required-timeout"],
    )
    route_metric: Optional[int] = Field(
        alias="route-metric", default=NM_SETTING_IPCONFIG_DEFAULTS["route-metric"]
    )
    route_table: Optional[int] = Field(
        alias="route-table", default=NM_SETTING_IPCONFIG_DEFAULTS["route-table"]
    )
    routes: Optional[List[str]] = None


class ConnectionSettingsIP4ConfigModel(ConnectionSettingsIPConfigModel):
    """Model for the 'ipv4' setting of a NetworkManager Connection"""

    dhcp_client_id: Optional[str] = Field(alias="dhcp-client-id", default=None)
    dhcp_fqdn: Optional[str] = Field(alias="dhcp-fqdn", default=None)
    dhcp_vendor_class_identifier: Optional[str] = Field(
        alias="dhcp-vendor-class-identifier", default=None
    )
    link_local: Optional[int] = Field(
        alias="link-local", default=NM_SETTING_IP4CONFIG_DEFAULTS["link-local"]
    )


class ConnectionSettingsIP6ConfigModel(ConnectionSettingsIPConfigModel):
    """Model for the 'ipv6' setting of a NetworkManager Connection"""

    addr_gen_mode: Optional[int] = Field(
        alias="addr-gen-mode", default=NM_SETTING_IP6CONFIG_DEFAULTS["addr-gen-mode"]
    )
    dhcp_duid: Optional[str] = Field(alias="dhcp-duid", default=None)
    ip6_privacy: Optional[int] = Field(
        alias="ip6-privacy", default=NM_SETTING_IP6CONFIG_DEFAULTS["ip6-privacy"]
    )
    mtu: Optional[int] = Field(default=NM_SETTING_IP6CONFIG_DEFAULTS["mtu"])
    ra_timeout: Optional[int] = Field(
        alias="ra-timeout", default=NM_SETTING_IP6CONFIG_DEFAULTS["ra-timeout"]
    )
    token: Optional[str] = None


class ConnectionSettingsWiredModel(BaseModel):
    """Model for the '802-3-ethernet' setting of a NetworkManager Connection"""

    accept_all_mac_addresses: Optional[bool] = Field(
        alias="accept-all-mac-addresses",
        default=NM_SETTING_WIRED_DEFAULTS["accept-all-mac-addresses"],
    )
    auto_negotiate: Optional[bool] = Field(
        alias="auto-negotiate", default=NM_SETTING_WIRED_DEFAULTS["auto-negotiate"]
    )
    cloned_mac_address: Optional[str] = Field(alias="cloned-mac-address", default=None)
    duplex: Optional[str] = None
    generate_mac_address_mask: Optional[str] = Field(
        alias="generate-mac-address-mask", default=None
    )
    mac_address: Optional[str] = Field(alias="mac-address", default=None)
    mac_address_blacklist: Optional[List[str]] = Field(
        alias="mac-address-blacklist",
        default=NM_SETTING_WIRED_DEFAULTS["mac-address-blacklist"],
    )
    mtu: Optional[int] = Field(default=NM_SETTING_WIRED_DEFAULTS["mtu"])
    port: Optional[str] = None
    s390_nettype: Optional[str] = Field(alias="s390-nettype", default=None)
    s390_options: Optional[str] = Field(alias="s390-options", default=None)
    s390_subchannels: Optional[List[str]] = Field(
        alias="s390-subchannels", default=NM_SETTING_WIRED_DEFAULTS["s390-subchannels"]
    )
    speed: Optional[int] = Field(default=NM_SETTING_WIRED_DEFAULTS["speed"])
    wake_on_lan: Optional[int] = Field(
        alias="wake-on-lan", default=NM_SETTING_WIRED_DEFAULTS["wake-on-lan"]
    )
    wake_on_lan_password: Optional[str] = Field(
        alias="wake-on-lan-password", default=None
    )


class ConnectionSettingsWirelessModel(BaseModel):
    """Model for the '802-11-wireless' setting of a NetworkManager Connection"""

    ap_isolation: Optional[int] = Field(
        alias="ap-isolation", default=NM_SETTING_WIRELESS_DEFAULTS["ap-isolation"]
    )
    band: Optional[str] = None
    bssid: Optional[str] = None
    channel: Optional[int] = Field(default=NM_SETTING_WIRELESS_DEFAULTS["channel"])
    cloned_mac_address: Optional[str] = Field(alias="cloned-mac-address", default=None)
    generate_mac_address_mask: Optional[str] = Field(
        alias="generate-mac-address-mask", default=None
    )
    hidden: Optional[bool] = Field(default=NM_SETTING_WIRELESS_DEFAULTS["hidden"])
    mac_address: Optional[str] = Field(alias="mac-address", default=None)
    mac_address_blacklist: Optional[List[str]] = Field(
        alias="mac-address-blacklist",
        default=NM_SETTING_WIRELESS_DEFAULTS["mac-address-blacklist"],
    )
    mac_address_randomization: Optional[int] = Field(
        alias="mac-address-randomization",
        default=NM_SETTING_WIRELESS_DEFAULTS["mac-address-randomization"],
    )
    mode: Optional[str] = None
    mtu: Optional[int] = Field(default=NM_SETTING_WIRELESS_DEFAULTS["mtu"])
    powersave: Optional[int] = Field(default=NM_SETTING_WIRELESS_DEFAULTS["powersave"])
    rate: Optional[int] = Field(default=NM_SETTING_WIRELESS_DEFAULTS["rate"])
    seen_bssids: Optional[List[str]] = Field(
        alias="seen-bssids", default=NM_SETTING_WIRELESS_DEFAULTS["seen-bssids"]
    )
    ssid: Optional[str] = None
    tx_power: Optional[int] = Field(
        alias="tx-power", default=NM_SETTING_WIRELESS_DEFAULTS["tx-power"]
    )
    wake_on_wlan: Optional[int] = Field(
        alias="wake-on-wlan", default=NM_SETTING_WIRELESS_DEFAULTS["wake-on-wlan"]
    )


class ConnectionSettingsWirelessSecurityModel(BaseModel):
    """Model for the '802-11-wireless-security' setting of a NetworkManager Connection"""

    auth_alg: Optional[str] = Field(
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["auth-alg"]
    )
    fils: Optional[int] = Field(default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["fils"])
    group: Optional[List[str]] = Field(
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["group"]
    )
    key_mgmt: Optional[str] = Field(alias="key-mgmt", default=None)
    leap_password: Optional[str] = Field(alias="leap-password", default=None)
    leap_password_flags: Optional[int] = Field(
        alias="leap-password-flags",
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["leap-password-flags"],
    )
    leap_username: Optional[str] = Field(alias="leap-username", default=None)
    pairwise: Optional[List[str]] = Field(
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["pairwise"]
    )
    pmf: Optional[int] = Field(default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["pmf"])
    proto: Optional[List[str]] = Field(
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["proto"]
    )
    psk: Optional[str] = None
    psk_flags: Optional[int] = Field(
        alias="psk-flags", default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["psk-flags"]
    )
    wep_key0: Optional[str] = Field(alias="wep-key0", default=None)
    wep_key1: Optional[str] = Field(alias="wep-key1", default=None)
    wep_key2: Optional[str] = Field(alias="wep-key2", default=None)
    wep_key3: Optional[str] = Field(alias="wep-key3", default=None)
    wep_key_flags: Optional[int] = Field(
        alias="wep-key-flags",
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["wep-key-flags"],
    )
    wep_key_type: Optional[int] = Field(
        alias="wep-key-type",
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["wep-key-type"],
    )
    wep_tx_keyidx: Optional[int] = Field(
        alias="wep-tx-keyidx",
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["wep-tx-keyidx"],
    )
    wps_method: Optional[int] = Field(
        alias="wps-method", default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["wps-method"]
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
