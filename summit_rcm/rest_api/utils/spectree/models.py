"""Module to hold SpecTree Models"""

from typing import Any, Dict, List, Optional
try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field
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


class BadRequestErrorResponseModel(BaseModel):
    """Model for a 400 (Bad Request) error response"""

    __root__: None


class UnauthorizedErrorResponseModel(BaseModel):
    """Model for a 401 (Unauthorized) error response"""

    __root__: None


class ForbiddenErrorResponseModel(BaseModel):
    """Model for a 403 (Forbidden) error response"""

    __root__: None


class NotFoundErrorResponseModel(BaseModel):
    """Model for a 404 (Not Found) error response"""

    __root__: None


class ConflictErrorResponseModel(BaseModel):
    """Model for a 409 (Conflict) error response"""

    __root__: None


class LengthRequiredErrorResponseModel(BaseModel):
    """Model for a 411 (Length Required) error response"""

    __root__: None


class UnsupportedMediaTypeErrorResponseModel(BaseModel):
    """Model for a 415 (Unsupported Media Type) error response"""

    __root__: None


class InternalServerErrorResponseModel(BaseModel):
    """Model for a 500 (Internal Server Error) error response"""

    __root__: None


class DefaultResponseModelLegacy(BaseModel):
    """Model for the default response (legacy)"""

    SDCERR: int
    InfoMsg: str = Field(default="")


class UserResponseModel(BaseModel):
    """Model for a user"""

    username: str
    permissions: str


class UsersResponseModel(BaseModel):
    """Model for all users"""

    __root__: List[UserResponseModel]


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

    zone: Optional[str]
    datetime: Optional[str]


class SetDateTimeRequestModelLegacy(BaseModel):
    """Model for a request to set the current date/time info (legacy)"""

    zone: Optional[str]
    datetime: Optional[str]
    method: Optional[str]


class SetDateTimeResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for the response to a request to set the current date/time info (legacy)"""

    time: Optional[str]


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


class LogsDataResponseModel(BaseModel):
    """Model for log data response"""

    __root__: List[LogData]


class LogsDataResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for log data response (legacy)"""

    count: Optional[int]
    log: Optional[List[LogData]]


class LogVerbosity(BaseModel):
    """Model for a log verbosity request/response"""

    suppDebugLevel: SupplicantLogLevelEnum
    driverDebugLevel: DriverLogLevelEnum


class LogVerbosityResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for a log verbosity response (legacy)"""

    suppDebugLevel: Optional[str]
    driverDebugLevel: Optional[int]
    Errormsg: Optional[str]


class ChronyNTPSource(BaseModel):
    """Model for a chrony NTP source"""

    address: str
    type: str


class ChronyNTPSources(BaseModel):
    """Model for a Chrony NTP sources request/response"""

    __root__: List[ChronyNTPSource]


class PowerState(BaseModel):
    """Model for power state request/response"""

    state: PowerStateEnum


class FirmwareUpdateStatus(BaseModel):
    """Model for firmware update status request/response"""

    status: Optional[SummitRCMUpdateStatus]
    url: Optional[str]
    image: Optional[str]


class FirmwareUpdateModelLegacy(BaseModel):
    """Model for firmware update status request/response (legacy)"""

    url: Optional[str]
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


class AccessPoint(BaseModel):
    """Model for an access point"""

    ssid: Optional[str]
    hwAddress: Optional[str]
    strength: Optional[int]
    maxBitrate: Optional[int]
    frequency: Optional[int]
    flags: Optional[int]
    wpaFlags: Optional[int]
    rsnFlags: Optional[int]
    lastSeen: Optional[int]
    security: Optional[str]
    keymgmt: Optional[str]


class AccessPointLegacy(BaseModel):
    """Model for an access point (legacy)"""

    SSID: Optional[str]
    HwAddress: Optional[str]
    Strength: Optional[int]
    MaxBitrate: Optional[int]
    Frequency: Optional[int]
    Flags: Optional[int]
    WpaFlags: Optional[int]
    RsnFlags: Optional[int]
    LastSeen: Optional[int]
    Security: Optional[str]
    Keymgmt: Optional[str]


class ActiveAccessPoint(AccessPoint):
    """Model for an active access point"""

    signal: Optional[float]


class ActiveAccessPointLegacy(BaseModel):
    """Model for an active access point (legacy)"""

    Ssid: Optional[str]
    HwAddress: Optional[str]
    Maxbitrate: Optional[int]
    Flags: Optional[int]
    Wpaflags: Optional[int]
    Rsnflags: Optional[int]
    Strength: Optional[int]
    Frequency: Optional[int]
    Signal: Optional[float]


class AccessPoints(BaseModel):
    """Model for an access points response"""

    __root__: List[AccessPoint]


class AccessPointsResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for an access points response (legacy)"""

    count: int
    accesspoints: List[AccessPointLegacy]


class AccessPointScanRequestReponseModel(BaseModel):
    """Model for the response to a request for an access point scan"""

    scanRequested: bool


class CertificateFiles(BaseModel):
    """Model for certificate files response"""

    __root__: List[str]


class CertificateInfoRequest(BaseModel):
    """Model for a certificate info request"""

    password: Optional[str]


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

    name: Optional[str]
    password: Optional[str]


class CertificateInfoResponseLegacy(DefaultResponseModelLegacy):
    """Model for a certificate info response (legacy)"""

    cert_info: Optional[CertificateInfoResponse]
    files: Optional[List[str]]
    count: Optional[int]


class CertificateUploadRequestFormModel(BaseModel):
    """Model for a request to upload a certificate"""

    file: BaseFile


class FileUploadRequestModelLegacy(BaseModel):
    """Model for a request to upload a file (legacy)"""

    type: str
    password: Optional[str]
    file: BaseFile


class FileDownloadQueryModelLegacy(BaseModel):
    """Model for a file download query (legacy)"""

    type: str
    password: Optional[str]


class FileDeleteQueryModelLegacy(BaseModel):
    """Model for a file delete query (legacy)"""

    type: str
    file: str


class FileInfoRequestQueryModelLegacy(BaseModel):
    """Model for a file info request query (legacy)"""

    type: str
    password: Optional[str]


class FileInfoResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for a file info response (legacy)"""

    files: Optional[List[str]]
    count: Optional[int]


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
    id: Optional[str]
    interface_name: Optional[str] = Field(alias="interface-name")
    lldp: Optional[int] = Field(default=NM_SETTING_CONNECTION_DEFAULTS["lldp"])
    llmnr: Optional[int] = Field(default=NM_SETTING_CONNECTION_DEFAULTS["llmnr"])
    master: Optional[str]
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
    slave_type: Optional[str] = Field(alias="slave-type")
    stable_id: Optional[str] = Field(alias="stable-id")
    timestamp: Optional[int] = Field(
        default=NM_SETTING_CONNECTION_DEFAULTS["timestamp"]
    )
    type: Optional[str]
    uuid: Optional[str]
    wait_activation_delay: Optional[int] = Field(
        alias="wait-activation-delay",
        default=NM_SETTING_CONNECTION_DEFAULTS["wait-activation-delay"],
    )
    wait_device_timeout: Optional[int] = Field(
        alias="wait-device-timeout",
        default=NM_SETTING_CONNECTION_DEFAULTS["wait-device-timeout"],
    )
    zone: Optional[str]


class ConnectionSettings8021xModel(BaseModel):
    """Model for the '802-1x' setting of a NetworkManager Connection"""

    altsubject_matches: Optional[List[str]] = Field(
        alias="altsubject-matches",
        default=NM_SETTING_8021X_DEFAULTS["altsubject-matches"],
    )
    anonymous_identity: Optional[str] = Field(alias="anonymous-identity")
    auth_timeout: Optional[int] = Field(
        alias="auth-timeout", default=NM_SETTING_8021X_DEFAULTS["auth-timeout"]
    )
    ca_cert: Optional[str] = Field(alias="ca-cert")
    ca_cert_password: Optional[str] = Field(alias="ca-cert-password")
    ca_cert_password_flags: Optional[int] = Field(
        alias="ca-cert-password-flags",
        default=NM_SETTING_8021X_DEFAULTS["ca-cert-password-flags"],
    )
    ca_path: Optional[str] = Field(alias="ca-path")
    client_cert: Optional[str] = Field(alias="client-cert")
    client_cert_password: Optional[str] = Field(alias="client-cert-password")
    client_cert_password_flags: Optional[int] = Field(
        alias="client-cert-password-flags",
        default=NM_SETTING_8021X_DEFAULTS["client-cert-password-flags"],
    )
    domain_match: Optional[str] = Field(alias="domain-match")
    domain_suffix_match: Optional[str] = Field(alias="domain-suffix-match")
    eap: Optional[List[str]] = Field(default=NM_SETTING_8021X_DEFAULTS["eap"])
    identity: Optional[str]
    optional: Optional[bool] = Field(default=NM_SETTING_8021X_DEFAULTS["optional"])
    pac_file: Optional[str] = Field(alias="pac-file")
    password: Optional[str]
    password_flags: Optional[int] = Field(
        default=NM_SETTING_8021X_DEFAULTS["password-flags"]
    )
    password_raw: Optional[str] = Field(alias="password-raw")
    password_raw_flags: Optional[int] = Field(
        alias="password-raw-flags",
        default=NM_SETTING_8021X_DEFAULTS["password-raw-flags"],
    )
    phase1_auth_flags: Optional[int] = Field(
        alias="phase1-auth-flags",
        default=NM_SETTING_8021X_DEFAULTS["phase1-auth-flags"],
    )
    phase1_fast_provisioning: Optional[str] = Field(
        alias="phase1-fast-provisioning",
    )
    phase1_peaplabel: Optional[str] = Field(alias="phase1-peaplabel")
    phase1_peapver: Optional[str] = Field(alias="phase1-peapver")
    phase2_altsubject_matches: Optional[List[str]] = Field(
        alias="phase2-altsubject-matches",
        default=NM_SETTING_8021X_DEFAULTS["phase2-altsubject-matches"],
    )
    phase2_auth: Optional[str] = Field(alias="phase2-auth")
    phase2_autheap: Optional[str] = Field(alias="phase2-autheap")
    phase2_ca_cert: Optional[str] = Field(alias="phase2-ca-cert")
    phase2_ca_cert_password: Optional[str] = Field(alias="phase2-ca-cert-password")
    phase2_ca_cert_password_flags: Optional[int] = Field(
        alias="phase2-ca-cert-password-flags",
        default=NM_SETTING_8021X_DEFAULTS["phase2-ca-cert-password-flags"],
    )
    phase2_ca_path: Optional[str] = Field(alias="phase2-ca-path")
    phase2_client_cert: Optional[str] = Field(alias="phase2-client-cert")
    phase2_client_cert_password: Optional[str] = Field(
        alias="phase2-client-cert-password"
    )
    phase2_client_cert_password_flags: Optional[int] = Field(
        alias="phase2-client-cert-password-flags",
        default=NM_SETTING_8021X_DEFAULTS["phase2-client-cert-password-flags"],
    )
    phase2_domain_match: Optional[str] = Field(alias="phase2-domain-match")
    phase2_domain_suffix_match: Optional[str] = Field(
        alias="phase2-domain-suffix-match"
    )
    phase2_private_key: Optional[str] = Field(alias="phase2-private-key")
    phase2_private_key_password: Optional[str] = Field(
        alias="phase2-private-key-password"
    )
    phase2_private_key_password_flags: Optional[int] = Field(
        alias="phase2-private-key-password-flags",
        default=NM_SETTING_8021X_DEFAULTS["phase2-private-key-password-flags"],
    )
    phase2_subject_match: Optional[str] = Field(alias="phase2-subject-match")
    pin: Optional[str]
    pin_flags: Optional[int] = Field(
        alias="pin-flags", default=NM_SETTING_8021X_DEFAULTS["pin-flags"]
    )
    private_key: Optional[str] = Field(alias="private-key")
    private_key_password: Optional[str] = Field(alias="private-key-password")
    private_key_password_flags: Optional[int] = Field(
        alias="private-key-password-flags",
        default=NM_SETTING_8021X_DEFAULTS["private-key-password-flags"],
    )
    subject_match: Optional[str] = Field(alias="subject-match")
    system_ca_certs: Optional[bool] = Field(
        alias="system-ca-certs", default=NM_SETTING_8021X_DEFAULTS["system-ca-certs"]
    )


class ConnectionSettingsGsmModel(BaseModel):
    """Model for the 'gsm' setting of a NetworkManager Connection"""

    apn: Optional[str]
    auto_config: Optional[bool] = Field(alias="auto-config", default=False)
    device_id: Optional[str] = Field(alias="device-id")
    home_only: Optional[bool] = Field(alias="home-only", default=False)
    mtu: Optional[int] = Field(default=0)
    network_id: Optional[str] = Field(alias="network-id")
    number: Optional[str]
    password: Optional[str]
    password_flags: Optional[int] = Field(
        alias="password-flags", default=NMSettingSecretFlags.NM_SETTING_SECRET_FLAG_NONE
    )
    pin: Optional[str]
    pin_flags: Optional[int] = Field(
        alias="pin-flags", default=NMSettingSecretFlags.NM_SETTING_SECRET_FLAG_NONE
    )
    sim_id: Optional[str] = Field(alias="sim-id")
    sim_operator_id: Optional[str] = Field(alias="sim-operator-id")
    username: Optional[str]


class ConnectionSettingsIPConfigModel(BaseModel):
    """Base model for an IP config setting of a NetworkManager Connection"""

    addresses: Optional[List[str]]
    auto_route_ext_gw: Optional[bool] = Field(
        alias="auto-route-ext-gw",
        default=NM_SETTING_IPCONFIG_DEFAULTS["auto-route-ext-gw"],
    )
    dad_timeout: Optional[int] = Field(
        alias="dad-timeout", default=NM_SETTING_IPCONFIG_DEFAULTS["dad-timeout"]
    )
    dhcp_hostname: Optional[str] = Field(alias="dhcp-hostname")
    dhcp_hostname_flags: Optional[int] = Field(
        alias="dhcp-hostname-flags",
        default=NM_SETTING_IPCONFIG_DEFAULTS["dhcp-hostname-flags"],
    )
    dhcp_iaid: Optional[str] = Field(alias="dhcp-iaid")
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
    gateway: Optional[str]
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
    method: Optional[str]
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
    routes: Optional[List[str]]


class ConnectionSettingsIP4ConfigModel(ConnectionSettingsIPConfigModel):
    """Model for the 'ipv4' setting of a NetworkManager Connection"""

    dhcp_client_id: Optional[str] = Field(alias="dhcp-client-id")
    dhcp_fqdn: Optional[str] = Field(alias="dhcp-fqdn")
    dhcp_vendor_class_identifier: Optional[str] = Field(
        alias="dhcp-vendor-class-identifier"
    )
    link_local: Optional[int] = Field(
        alias="link-local", default=NM_SETTING_IP4CONFIG_DEFAULTS["link-local"]
    )


class ConnectionSettingsIP6ConfigModel(ConnectionSettingsIPConfigModel):
    """Model for the 'ipv6' setting of a NetworkManager Connection"""

    addr_gen_mode: Optional[int] = Field(
        alias="addr-gen-mode", default=NM_SETTING_IP6CONFIG_DEFAULTS["addr-gen-mode"]
    )
    dhcp_duid: Optional[str] = Field(alias="dhcp-duid")
    ip6_privacy: Optional[int] = Field(
        alias="ip6-privacy", default=NM_SETTING_IP6CONFIG_DEFAULTS["ip6-privacy"]
    )
    mtu: Optional[int] = Field(default=NM_SETTING_IP6CONFIG_DEFAULTS["mtu"])
    ra_timeout: Optional[int] = Field(
        alias="ra-timeout", default=NM_SETTING_IP6CONFIG_DEFAULTS["ra-timeout"]
    )
    token: Optional[str]


class ConnectionSettingsWiredModel(BaseModel):
    """Model for the '802-3-ethernet' setting of a NetworkManager Connection"""

    accept_all_mac_addresses: Optional[bool] = Field(
        alias="accept-all-mac-addresses",
        default=NM_SETTING_WIRED_DEFAULTS["accept-all-mac-addresses"],
    )
    auto_negotiate: Optional[bool] = Field(
        alias="auto-negotiate", default=NM_SETTING_WIRED_DEFAULTS["auto-negotiate"]
    )
    cloned_mac_address: Optional[str] = Field(alias="cloned-mac-address")
    duplex: Optional[str]
    generate_mac_address_mask: Optional[str] = Field(
        alias="generate-mac-address-mask",
    )
    mac_address: Optional[str] = Field(alias="mac-address")
    mac_address_blacklist: Optional[List[str]] = Field(
        alias="mac-address-blacklist",
        default=NM_SETTING_WIRED_DEFAULTS["mac-address-blacklist"],
    )
    mtu: Optional[int] = Field(default=NM_SETTING_WIRED_DEFAULTS["mtu"])
    port: Optional[str]
    s390_nettype: Optional[str] = Field(alias="s390-nettype")
    s390_options: Optional[str] = Field(alias="s390-options")
    s390_subchannels: Optional[List[str]] = Field(
        alias="s390-subchannels", default=NM_SETTING_WIRED_DEFAULTS["s390-subchannels"]
    )
    speed: Optional[int] = Field(default=NM_SETTING_WIRED_DEFAULTS["speed"])
    wake_on_lan: Optional[int] = Field(
        alias="wake-on-lan", default=NM_SETTING_WIRED_DEFAULTS["wake-on-lan"]
    )
    wake_on_lan_password: Optional[str] = Field(alias="wake-on-lan-password")


class ConnectionSettingsWirelessModel(BaseModel):
    """Model for the '802-11-wireless' setting of a NetworkManager Connection"""

    ap_isolation: Optional[int] = Field(
        alias="ap-isolation", default=NM_SETTING_WIRELESS_DEFAULTS["ap-isolation"]
    )
    band: Optional[str]
    bssid: Optional[str]
    channel: Optional[int] = Field(default=NM_SETTING_WIRELESS_DEFAULTS["channel"])
    cloned_mac_address: Optional[str] = Field(alias="cloned-mac-address")
    generate_mac_address_mask: Optional[str] = Field(
        alias="generate-mac-address-mask",
    )
    hidden: Optional[bool] = Field(default=NM_SETTING_WIRELESS_DEFAULTS["hidden"])
    mac_address: Optional[str] = Field(alias="mac-address")
    mac_address_blacklist: Optional[List[str]] = Field(
        alias="mac-address-blacklist",
        default=NM_SETTING_WIRELESS_DEFAULTS["mac-address-blacklist"],
    )
    mac_address_randomization: Optional[int] = Field(
        alias="mac-address-randomization",
        default=NM_SETTING_WIRELESS_DEFAULTS["mac-address-randomization"],
    )
    mode: Optional[str]
    mtu: Optional[int] = Field(default=NM_SETTING_WIRELESS_DEFAULTS["mtu"])
    powersave: Optional[int] = Field(default=NM_SETTING_WIRELESS_DEFAULTS["powersave"])
    rate: Optional[int] = Field(default=NM_SETTING_WIRELESS_DEFAULTS["rate"])
    seen_bssids: Optional[List[str]] = Field(
        alias="seen-bssids", default=NM_SETTING_WIRELESS_DEFAULTS["seen-bssids"]
    )
    ssid: Optional[str]
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
    key_mgmt: Optional[str] = Field(alias="key-mgmt")
    leap_password: Optional[str] = Field(alias="leap-password")
    leap_password_flags: Optional[int] = Field(
        alias="leap-password-flags",
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["leap-password-flags"],
    )
    leap_username: Optional[str] = Field(alias="leap-username")
    pairwise: Optional[List[str]] = Field(
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["pairwise"]
    )
    pmf: Optional[int] = Field(default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["pmf"])
    proto: Optional[List[str]] = Field(
        default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["proto"]
    )
    psk: Optional[str]
    psk_flags: Optional[int] = Field(
        alias="psk-flags", default=NM_SETTING_WIRELESS_SECURITY_DEFAULTS["psk-flags"]
    )
    wep_key0: Optional[str] = Field(alias="wep-key0")
    wep_key1: Optional[str] = Field(alias="wep-key1")
    wep_key2: Optional[str] = Field(alias="wep-key2")
    wep_key3: Optional[str] = Field(alias="wep-key3")
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
    enterprise_auth: Optional[ConnectionSettings8021xModel] = Field(alias="802-1x")
    gsm: Optional[ConnectionSettingsGsmModel]
    ipv4: Optional[ConnectionSettingsIP4ConfigModel]
    ipv6: Optional[ConnectionSettingsIP6ConfigModel]
    wired: Optional[ConnectionSettingsWiredModel] = Field(alias="802-3-ethernet")
    wireless: Optional[ConnectionSettingsWirelessModel] = Field(alias="802-11-wireless")
    wireless_security: Optional[ConnectionSettingsWirelessSecurityModel] = Field(
        alias="802-11-wireless-security"
    )
    activated: Optional[bool]


class ConnectionProfileLegacy(DefaultResponseModelLegacy):
    """Model for a connection profile (legacy)"""

    connection: Optional[ConnectionProfile]


class ConnectionProfiles(BaseModel):
    """Model for response to request for all connection profiles"""

    __root__: List[ConnectionProfileInfo]


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


class NetworkInterfacesResponseModel(BaseModel):
    """Model for response to request for all network interfaces"""

    __root__: List[str]


class NetworkInterfacesResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for response to request for all network interfaces (legacy)"""

    interfaces: List[str]


class NetworkInterfaceStatus(BaseModel):
    """Model for a network interface status"""

    state: Optional[int]
    stateText: Optional[str]
    mtu: Optional[int]
    deviceType: Optional[int]
    deviceTypeText: Optional[str]


class NetworkInterfaceStatusLegacy(BaseModel):
    """Model for a network interface status (legacy)"""

    State: Optional[int]
    StateText: Optional[str]
    Mtu: Optional[int]
    DeviceType: Optional[int]
    DeviceTypeText: Optional[str]


class NetworkInterfaceWirelessProperties(BaseModel):
    """Model for wireless properties of a network interface"""

    bitrate: int
    permHwAddress: str
    mode: int
    regDomain: str
    hwAddress: str


class NetworkInterfaceWirelessPropertiesLegacy(BaseModel):
    """Model for wireless properties of a network interface (legacy)"""

    Bitrate: int
    PermHwAddress: str
    Mode: int
    RegDomain: str
    HwAddress: str


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

    addressData: Optional[List[AddressDataModel]]
    routeData: Optional[List[RouteDataModel]]
    gateway: Optional[str]
    domains: Optional[List[str]]
    nameservers: Optional[List[str]]
    winsServers: Optional[List[str]]


class IP4ConfigModelLegacy(BaseModel):
    """Model for the IPv4 configuration (legacy)"""

    Addresses: Optional[Dict[str, str]]
    AddressData: Optional[List[AddressDataModel]]
    Routes: Optional[Dict[str, str]]
    RouteData: Optional[List[RouteDataModelLegacy]]
    Gateway: Optional[str]
    Domains: Optional[List[str]]
    NameserverData: Optional[List[str]]
    WinsServerData: Optional[List[str]]


class IP6ConfigModel(BaseModel):
    """Model for the IPv6 configuration"""

    addressData: Optional[List[AddressDataModel]]
    routeData: Optional[List[RouteDataModel]]
    gateway: Optional[str]
    domains: Optional[List[str]]
    nameservers: Optional[List[str]]


class IP6ConfigModelLegacy(BaseModel):
    """Model for the IPv6 configuration (legacy)"""

    Addresses: Optional[Dict[str, str]]
    AddressData: Optional[List[AddressDataModel]]
    Routes: Optional[Dict[str, str]]
    RouteData: Optional[List[RouteDataModelLegacy]]
    Gateway: Optional[str]
    Domains: Optional[List[str]]
    NameserverData: Optional[List[str]]
    WinsServerData: Optional[List[str]]


class DhcpConfigModel(BaseModel):
    """Model for the DHCP configuration"""

    options: Optional[Dict[str, str]]


class DhcpConfigModelLegacy(BaseModel):
    """Model for the DHCP configuration (legacy)"""

    Options: Optional[Dict[str, str]]


class NetworkInterfaceResponseModel(BaseModel):
    """Model for response to request for a specific network interface"""

    status: Optional[NetworkInterfaceStatus]
    ip4Config: Optional[IP4ConfigModel]
    ip6Config: Optional[IP6ConfigModel]
    dhcp4Config: Optional[DhcpConfigModel]
    dhcp6Config: Optional[DhcpConfigModel]
    wireless: Optional[NetworkInterfaceWirelessProperties]
    activeAccessPoint: Optional[ActiveAccessPoint]
    wired: Optional[NetworkInterfaceWiredProperties]
    udi: Optional[str]
    path: Optional[str]
    interface: Optional[str]
    ipInterface: Optional[str]
    driver: Optional[str]
    driverVersion: Optional[str]
    firmwareVersion: Optional[str]
    capabilities: Optional[int]
    stateReason: Optional[int]
    activeConnection: Optional[ConnectionSettingsConnectionModel]
    managed: Optional[bool] = Field(default=False)
    autoconnect: Optional[bool]
    firmwareMissing: Optional[bool] = Field(default=False)
    nmPluginMissing: Optional[bool] = Field(default=False)
    availableConnections: Optional[List[ConnectionSettingsConnectionModel]]
    physicalPortId: Optional[str]
    metered: Optional[int]
    meteredText: Optional[str]
    lldpNeighbors: Optional[List[str]]
    real: Optional[bool]
    ip4Connectivity: Optional[int]
    ip4ConnectivityText: Optional[str]
    ip6Connectivity: Optional[int]
    ip6ConnectivityText: Optional[str]
    interfaceFlags: Optional[int]


class NetworkInterfaceStatusModelLegacy(BaseModel):
    """Model for a network interface status (legacy)"""

    status: Optional[NetworkInterfaceStatusLegacy]
    ip4config: Optional[IP4ConfigModelLegacy]
    ip6config: Optional[IP6ConfigModelLegacy]
    dhcp4config: Optional[DhcpConfigModelLegacy]
    dhcp6config: Optional[DhcpConfigModelLegacy]
    wireless: Optional[NetworkInterfaceWirelessPropertiesLegacy]
    activeaccesspoint: Optional[ActiveAccessPointLegacy]
    wired: Optional[NetworkInterfaceWiredPropertiesLegacy]
    udi: Optional[str]
    path: Optional[str]
    interface: Optional[str]
    ip_interface: Optional[str]
    driver: Optional[str]
    driver_version: Optional[str]
    firmware_version: Optional[str]
    capabilities: Optional[int]
    state_reason: Optional[int]
    connection_active: Optional[ConnectionSettingsConnectionModel]
    managed: Optional[bool] = Field(default=False)
    autoconnect: Optional[bool]
    firmware_missing: Optional[bool] = Field(default=False)
    nm_plugin_missing: Optional[bool] = Field(default=False)
    available_connections: Optional[List[ConnectionSettingsConnectionModel]]
    physical_port_id: Optional[str]
    metered: Optional[int]
    metered_text: Optional[str]
    lldp_neighbors: Optional[List[str]]
    real: Optional[bool]
    ip4connectivity: Optional[int]
    ip4connectivity_text: Optional[str]
    ip6connectivity: Optional[int]
    ip6connectivity_text: Optional[str]
    interface_flags: Optional[int]


class NetworkInterfaceResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for response to request for a specific network interface (legacy)"""

    properties: Optional[NetworkInterfaceStatusModelLegacy]


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

    status: Optional[Dict[str, NetworkInterfaceResponseModel]]
    devices: Optional[int]


class NetworkStatusResponseModelLegacy(BaseModel):
    """Model for response to request for network status (legacy)"""

    status: Optional[Dict[str, NetworkInterfaceResponseModelLegacy]]
    devices: Optional[int]


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

    Definitions: Optional[DefinitionsModel]
