from socket import inet_pton, AF_INET, AF_INET6
from sys import byteorder
from typing import Any, Dict, List
from enum import IntFlag, IntEnum, unique
import os

try:
    from dbus_fast import Message, MessageType, Variant
    from summit_rcm.dbus_manager import DBusManager
except ImportError as error:
    # Ignore the error if the dbus_fast module is not available if generating documentation
    if os.environ.get("DOCS_GENERATION") != "True":
        raise error
import summit_rcm.definition
from summit_rcm.utils import Singleton


@unique
class NMDeviceInterfaceFlags(IntFlag):
    """
    Flags for a network interface.

    Since: 1.22
    """

    NM_DEVICE_INTERFACE_FLAG_NONE = 0
    """
    An alias for numeric zero, no flags set.
    """

    NM_DEVICE_INTERFACE_FLAG_UP = 0x1
    """
    The interface is enabled from the administrative point of view. Corresponds to kernel IFF_UP.
    """

    NM_DEVICE_INTERFACE_FLAG_LOWER_UP = 0x2
    """
    The physical link is up. Corresponds to kernel IFF_LOWER_UP.
    """

    NM_DEVICE_INTERFACE_FLAG_PROMISC = 0x4
    """
    Receive all packets. Corresponds to kernel IFF_PROMISC. Since: 1.32.
    """

    NM_DEVICE_INTERFACE_FLAG_CARRIER = 0x10000
    """
    The interface has carrier. In most cases this is equal to the value of
    NM_DEVICE_INTERFACE_FLAG_LOWER_UP. However some devices have a non-standard carrier detection
    mechanism.
    """

    NM_DEVICE_INTERFACE_FLAG_LLDP_CLIENT_ENABLED = 0x20000
    """
    The flag to indicate device LLDP status. Since: 1.32.
    """


@unique
class NMConnectivityState(IntEnum):
    NM_CONNECTIVITY_UNKNOWN = 0
    """
    Network connectivity is unknown. This means the connectivity checks are disabled (e.g. on server
    installations) or has not run yet. The graphical shell should assume the Internet connection
    might be available and not present a captive portal window.
    """

    NM_CONNECTIVITY_NONE = 1
    """
    The host is not connected to any network. There's no active connection that contains a default
    route to the internet and thus it makes no sense to even attempt a connectivity check. The
    graphical shell should use this state to indicate the network connection is unavailable.
    """

    NM_CONNECTIVITY_PORTAL = 2
    """
    The Internet connection is hijacked by a captive portal gateway. The graphical shell may open a
    sandboxed web browser window (because the captive portals typically attempt a man-in-the-middle
    attacks against the https connections) for the purpose of authenticating to a gateway and
    retrigger the connectivity check with CheckConnectivity() when the browser window is dismissed.
    """

    NM_CONNECTIVITY_LIMITED = 3
    """
    The host is connected to a network, does not appear to be able to reach the full Internet, but a
    captive portal has not been detected.
    """

    NM_CONNECTIVITY_FULL = 4
    """
    The host is connected to a network, and appears to be able to reach the full Internet.
    """


@unique
class NMDeviceStateReason(IntEnum):
    """
    Device state change reason codes
    """

    NM_DEVICE_STATE_REASON_NONE = 0
    """
    No reason given
    """

    NM_DEVICE_STATE_REASON_UNKNOWN = 1
    """
    Unknown error
    """

    NM_DEVICE_STATE_REASON_NOW_MANAGED = 2
    """
    Device is now managed
    """

    NM_DEVICE_STATE_REASON_NOW_UNMANAGED = 3
    """
    Device is now unmanaged
    """

    NM_DEVICE_STATE_REASON_CONFIG_FAILED = 4
    """
    The device could not be readied for configuration
    """

    NM_DEVICE_STATE_REASON_IP_CONFIG_UNAVAILABLE = 5
    """
    IP configuration could not be reserved (no available address, timeout, etc)
    """

    NM_DEVICE_STATE_REASON_IP_CONFIG_EXPIRED = 6
    """
    The IP config is no longer valid
    """

    NM_DEVICE_STATE_REASON_NO_SECRETS = 7
    """
    Secrets were required, but not provided
    """

    NM_DEVICE_STATE_REASON_SUPPLICANT_DISCONNECT = 8
    """
    802.1x supplicant disconnected
    """

    NM_DEVICE_STATE_REASON_SUPPLICANT_CONFIG_FAILED = 9
    """
    802.1x supplicant configuration failed
    """

    NM_DEVICE_STATE_REASON_SUPPLICANT_FAILED = 10
    """
    802.1x supplicant failed
    """

    NM_DEVICE_STATE_REASON_SUPPLICANT_TIMEOUT = 11
    """
    802.1x supplicant took too long to authenticate
    """

    NM_DEVICE_STATE_REASON_PPP_START_FAILED = 12
    """
    PPP service failed to start
    """

    NM_DEVICE_STATE_REASON_PPP_DISCONNECT = 13
    """
    PPP service disconnected
    """

    NM_DEVICE_STATE_REASON_PPP_FAILED = 14
    """
    PPP failed
    """

    NM_DEVICE_STATE_REASON_DHCP_START_FAILED = 15
    """
    DHCP client failed to start
    """

    NM_DEVICE_STATE_REASON_DHCP_ERROR = 16
    """
    DHCP client error
    """

    NM_DEVICE_STATE_REASON_DHCP_FAILED = 17
    """
    DHCP client failed
    """

    NM_DEVICE_STATE_REASON_SHARED_START_FAILED = 18
    """
    Shared connection service failed to start
    """

    NM_DEVICE_STATE_REASON_SHARED_FAILED = 19
    """
    Shared connection service failed
    """

    NM_DEVICE_STATE_REASON_AUTOIP_START_FAILED = 20
    """
    AutoIP service failed to start
    """

    NM_DEVICE_STATE_REASON_AUTOIP_ERROR = 21
    """
    AutoIP service error
    """

    NM_DEVICE_STATE_REASON_AUTOIP_FAILED = 22
    """
    AutoIP service failed
    """

    NM_DEVICE_STATE_REASON_MODEM_BUSY = 23
    """
    The line is busy
    """

    NM_DEVICE_STATE_REASON_MODEM_NO_DIAL_TONE = 24
    """
    No dial tone
    """

    NM_DEVICE_STATE_REASON_MODEM_NO_CARRIER = 25
    """
    No carrier could be established
    """

    NM_DEVICE_STATE_REASON_MODEM_DIAL_TIMEOUT = 26
    """
    The dialing request timed out
    """

    NM_DEVICE_STATE_REASON_MODEM_DIAL_FAILED = 27
    """
    The dialing attempt failed
    """

    NM_DEVICE_STATE_REASON_MODEM_INIT_FAILED = 28
    """
    Modem initialization failed
    """

    NM_DEVICE_STATE_REASON_GSM_APN_FAILED = 29
    """
    Failed to select the specified APN
    """

    NM_DEVICE_STATE_REASON_GSM_REGISTRATION_NOT_SEARCHING = 30
    """
    Not searching for networks
    """

    NM_DEVICE_STATE_REASON_GSM_REGISTRATION_DENIED = 31
    """
    Network registration denied
    """

    NM_DEVICE_STATE_REASON_GSM_REGISTRATION_TIMEOUT = 32
    """
    Network registration timed out
    """

    NM_DEVICE_STATE_REASON_GSM_REGISTRATION_FAILED = 33
    """
    Failed to register with the requested network
    """

    NM_DEVICE_STATE_REASON_GSM_PIN_CHECK_FAILED = 34
    """
    PIN check failed
    """

    NM_DEVICE_STATE_REASON_FIRMWARE_MISSING = 35
    """
    Necessary firmware for the device may be missing
    """

    NM_DEVICE_STATE_REASON_REMOVED = 36
    """
    The device was removed
    """

    NM_DEVICE_STATE_REASON_SLEEPING = 37
    """
    NetworkManager went to sleep
    """

    NM_DEVICE_STATE_REASON_CONNECTION_REMOVED = 38
    """
    The device's active connection disappeared
    """

    NM_DEVICE_STATE_REASON_USER_REQUESTED = 39
    """
    Device disconnected by user or client
    """

    NM_DEVICE_STATE_REASON_CARRIER = 40
    """
    Carrier/link changed
    """

    NM_DEVICE_STATE_REASON_CONNECTION_ASSUMED = 41
    """
    The device's existing connection was assumed
    """

    NM_DEVICE_STATE_REASON_SUPPLICANT_AVAILABLE = 42
    """
    The supplicant is now available
    """

    NM_DEVICE_STATE_REASON_MODEM_NOT_FOUND = 43
    """
    The modem could not be found
    """

    NM_DEVICE_STATE_REASON_BT_FAILED = 44
    """
    The Bluetooth connection failed or timed out
    """

    NM_DEVICE_STATE_REASON_GSM_SIM_NOT_INSERTED = 45
    """
    GSM Modem's SIM Card not inserted
    """

    NM_DEVICE_STATE_REASON_GSM_SIM_PIN_REQUIRED = 46
    """
    GSM Modem's SIM Pin required
    """

    NM_DEVICE_STATE_REASON_GSM_SIM_PUK_REQUIRED = 47
    """
    GSM Modem's SIM Puk required
    """

    NM_DEVICE_STATE_REASON_GSM_SIM_WRONG = 48
    """
    GSM Modem's SIM wrong
    """

    NM_DEVICE_STATE_REASON_INFINIBAND_MODE = 49
    """
    InfiniBand device does not support connected mode
    """

    NM_DEVICE_STATE_REASON_DEPENDENCY_FAILED = 50
    """
    A dependency of the connection failed
    """

    NM_DEVICE_STATE_REASON_BR2684_FAILED = 51
    """
    Problem with the RFC 2684 Ethernet over ADSL bridge
    """

    NM_DEVICE_STATE_REASON_MODEM_MANAGER_UNAVAILABLE = 52
    """
    ModemManager not running
    """

    NM_DEVICE_STATE_REASON_SSID_NOT_FOUND = 53
    """
    The Wi-Fi network could not be found
    """

    NM_DEVICE_STATE_REASON_SECONDARY_CONNECTION_FAILED = 54
    """
    A secondary connection of the base connection failed
    """

    NM_DEVICE_STATE_REASON_DCB_FCOE_FAILED = 55
    """
    DCB or FCoE setup failed
    """

    NM_DEVICE_STATE_REASON_TEAMD_CONTROL_FAILED = 56
    """
    teamd control failed
    """

    NM_DEVICE_STATE_REASON_MODEM_FAILED = 57
    """
    Modem failed or no longer available
    """

    NM_DEVICE_STATE_REASON_MODEM_AVAILABLE = 58
    """
    Modem now ready and available
    """

    NM_DEVICE_STATE_REASON_SIM_PIN_INCORRECT = 59
    """
    SIM PIN was incorrect
    """

    NM_DEVICE_STATE_REASON_NEW_ACTIVATION = 60
    """
    New connection activation was enqueued
    """

    NM_DEVICE_STATE_REASON_PARENT_CHANGED = 61
    """
    the device's parent changed
    """

    NM_DEVICE_STATE_REASON_PARENT_MANAGED_CHANGED = 62
    """
    the device parent's management changed
    """

    NM_DEVICE_STATE_REASON_OVSDB_FAILED = 63
    """
    problem communicating with Open vSwitch database
    """

    NM_DEVICE_STATE_REASON_IP_ADDRESS_DUPLICATE = 64
    """
    a duplicate IP address was detected
    """

    NM_DEVICE_STATE_REASON_IP_METHOD_UNSUPPORTED = 65
    """
    The selected IP method is not supported
    """

    NM_DEVICE_STATE_REASON_SRIOV_CONFIGURATION_FAILED = 66
    """
    configuration of SR-IOV parameters failed
    """

    NM_DEVICE_STATE_REASON_PEER_NOT_FOUND = 67
    """
    The Wi-Fi P2P peer could not be found
    """


@unique
class NMDeviceCapabilities(IntFlag):
    """
    General device capability flags.
    """

    NM_DEVICE_CAP_NONE = 0x00000000
    """
    Device has no special capabilities
    """

    NM_DEVICE_CAP_NM_SUPPORTED = 0x00000001
    """
    NetworkManager supports this device
    """

    NM_DEVICE_CAP_CARRIER_DETECT = 0x00000002
    """
    This device can indicate carrier status
    """

    NM_DEVICE_CAP_IS_SOFTWARE = 0x00000004
    """
    This device is a software device
    """

    NM_DEVICE_CAP_SRIOV = 0x00000008
    """
    This device supports single-root I/O virtualization
    """


@unique
class NM80211Mode(IntEnum):
    """
    Indicates the 802.11 mode an access point or device is currently in.
    """

    NM_802_11_MODE_UNKNOWN = 0
    """
    The device or access point mode is unknown
    """

    NM_802_11_MODE_ADHOC = 1
    """
    For both devices and access point objects, indicates the object is part of an Ad-Hoc 802.11
    network without a central coordinating access point.
    """

    NM_802_11_MODE_INFRA = 2
    """
    The device or access point is in infrastructure mode. For devices, this indicates the device is
    an 802.11 client/station.  For access point objects, this indicates the object is an access
    point that provides connectivity to clients.
    """

    NM_802_11_MODE_AP = 3
    """
    The device is an access point/hotspot.  Not valid for access point objects; used only for
    hotspot mode on the local machine.
    """

    NM_802_11_MODE_MESH = 4
    """
    The device is a 802.11s mesh point. Since: 1.20.
    """


class NM80211ApSecurityFlags(IntFlag):
    """
    802.11 access point security and authentication flags.  These flags describe the current
    security requirements of an access point as determined from the access point's beacon.
    """

    NM_802_11_AP_SEC_NONE = 0x00000000
    """
    The access point has no special security requirements
    """

    NM_802_11_AP_SEC_PAIR_WEP40 = 0x00000001
    """
    40/64-bit WEP is supported for pairwise/unicast encryption
    """

    NM_802_11_AP_SEC_PAIR_WEP104 = 0x00000002
    """
    104/128-bit WEP is supported for pairwise/unicast encryption
    """

    NM_802_11_AP_SEC_PAIR_TKIP = 0x00000004
    """
    TKIP is supported for pairwise/unicast encryption
    """

    NM_802_11_AP_SEC_PAIR_CCMP = 0x00000008
    """
    AES/CCMP-128 is supported for pairwise/unicast encryption
    """

    NM_802_11_AP_SEC_GROUP_WEP40 = 0x00000010
    """
    40/64-bit WEP is supported for group/broadcast encryption
    """

    NM_802_11_AP_SEC_GROUP_WEP104 = 0x00000020
    """
    104/128-bit WEP is supported for group/broadcast encryption
    """

    NM_802_11_AP_SEC_GROUP_TKIP = 0x00000040
    """
    TKIP is supported for group/broadcast encryption
    """

    NM_802_11_AP_SEC_GROUP_CCMP = 0x00000080
    """
    AES/CCMP-128 is supported for group/broadcast encryption
    """

    NM_802_11_AP_SEC_KEY_MGMT_PSK = 0x00000100
    """
    WPA/RSN Pre-Shared Key encryption is supported
    """

    NM_802_11_AP_SEC_KEY_MGMT_802_1X = 0x00000200
    """
    802.1x authentication and key management is supported
    """

    NM_802_11_AP_SEC_KEY_MGMT_SAE = 0x00000400
    """
    WPA/RSN Simultaneous Authentication of Equals is supported
    """

    NM_802_11_AP_SEC_KEY_MGMT_OWE = 0x00000800
    """
    WPA/RSN Opportunistic Wireless Encryption is supported
    """

    NM_802_11_AP_SEC_KEY_MGMT_OWE_TM = 0x00001000
    """
    WPA/RSN Opportunistic Wireless Encryption transition mode is supported. Since: 1.26.
    """

    NM_802_11_AP_SEC_KEY_MGMT_EAP_SUITE_B_192 = 0x00002000
    """
    WPA3 Enterprise Suite-B 192 bit mode is supported. Since: 1.30.
    """

    NM_802_11_AP_SEC_KEY_MGMT_SUITE_B_192 = NM_802_11_AP_SEC_KEY_MGMT_EAP_SUITE_B_192
    """
    Same as NM_802_11_AP_SEC_KEY_MGMT_EAP_SUITE_B_192 Laird addition for backwards compatibility
    """

    NM_802_11_AP_SEC_PAIR_CCMP_256 = 0x00010000
    """
    AES/CCMP-256 is supported for pairwise/unicast encryption
    """

    NM_802_11_AP_SEC_PAIR_GCMP_128 = 0x00020000
    """
    AES/GCMP-128 is supported for pairwise/unicast encryption
    """

    NM_802_11_AP_SEC_PAIR_GCMP_256 = 0x00040000
    """
    AES/GCMP-256 is supported for pairwise/unicast encryption
    """

    NM_802_11_AP_SEC_GROUP_CCMP_256 = 0x00080000
    """
    AES/CCMP-256 is supported for group/broadcast encryption
    """

    NM_802_11_AP_SEC_GROUP_GCMP_128 = 0x00100000
    """
    AES/GCMP-128 is supported for group/broadcast encryption
    """

    NM_802_11_AP_SEC_GROUP_GCMP_256 = 0x00200000
    """
    AES/GCMP-256 is supported for group/broadcast encryption
    """

    NM_802_11_AP_SEC_KEY_MGMT_SUITE_B = 0x00400000
    """
    Suite-B authentication and key management is supported
    """

    NM_802_11_AP_SEC_KEY_MGMT_CCKM = 0x01000800
    """
    CCKM authentication and key management is supported
    """

    NM_802_11_AP_SEC_MGMT_GROUP_CMAC_128 = 0x02000000
    """
    BIP-CMAC-128 group management frame is supported
    """

    NM_802_11_AP_SEC_MGMT_GROUP_CMAC_256 = 0x04000000
    """
    BIP-CMAC-256 group management frame is supported
    """

    NM_802_11_AP_SEC_MGMT_GROUP_GMAC_128 = 0x08000000
    """
    BIP-GMAC-128 group management frame is supported
    """

    NM_802_11_AP_SEC_MGMT_GROUP_GMAC_256 = 0x10000000
    """
    BIP-GMAC-256 group management frame is supported
    """


@unique
class NM80211ApFlags(IntFlag):
    """
    802.11 access point flags.
    """

    NM_802_11_AP_FLAGS_NONE = 0x00000000
    """
    Access point has no special capabilities
    """

    NM_802_11_AP_FLAGS_PRIVACY = 0x00000001
    """
    Access point requires authentication and encryption (usually means WEP)
    """

    NM_802_11_AP_FLAGS_WPS = 0x00000002
    """
    Access point supports some WPS method
    """

    NM_802_11_AP_FLAGS_WPS_PBC = 0x00000004
    """
    Access point supports push-button WPS
    """

    NM_802_11_AP_FLAGS_WPS_PIN = 0x00000008
    """
    Access point supports PIN-based WPS
    """

    NM_802_11_AP_FLAGS_OWE_IE = 0x00000010
    """
    Access point has OWE IE
    """

    NM_802_11_AP_FLAGS_P2P_IE = 0x00000020
    """
    Access point has P2P IE
    """


@unique
class NMDeviceState(IntEnum):
    NM_DEVICE_STATE_UNKNOWN = 0
    """
    The device's state is unknown
    """

    NM_DEVICE_STATE_UNMANAGED = 10
    """
    The device is recognized, but not managed by NetworkManager
    """

    NM_DEVICE_STATE_UNAVAILABLE = 20
    """
    The device is managed by NetworkManager, but is not available for use.  Reasons may include the
    wireless switched off, missing firmware, no ethernet carrier, missing supplicant or modem
    manager, etc.
    """

    NM_DEVICE_STATE_DISCONNECTED = 30
    """
    The device can be activated, but is currently idle and not connected to a network.
    """

    NM_DEVICE_STATE_PREPARE = 40
    """
    The device is preparing the connection to the network. This may include operations like changing
    the MAC address, setting physical link properties, and anything else required to connect to the
    requested network.
    """

    NM_DEVICE_STATE_CONFIG = 50
    """
    The device is connecting to the requested network. This may include operations like associating
    with the Wi-Fi AP, dialing the modem, connecting to the remote Bluetooth device, etc.
    """

    NM_DEVICE_STATE_NEED_AUTH = 60
    """
    The device requires more information to continue connecting to the requested network. This
    includes secrets like WiFi passphrases, login passwords, PIN codes, etc.
    """

    NM_DEVICE_STATE_IP_CONFIG = 70
    """
    The device is requesting IPv4 and/or IPv6 addresses and routing information from the network.
    """

    NM_DEVICE_STATE_IP_CHECK = 80
    """
    The device is checking whether further action is required for the requested network connection.
    This may include checking whether only local network access is available, whether a captive
    portal is blocking access to the Internet, etc.
    """

    NM_DEVICE_STATE_SECONDARIES = 90
    """
    The device is waiting for a secondary connection (like a VPN) which must activated before the
    device can be activated
    """

    NM_DEVICE_STATE_ACTIVATED = 100
    """
    The device has a network connection, either local or global.
    """

    NM_DEVICE_STATE_DEACTIVATING = 110
    """
    A disconnection from the current network connection was requested, and the device is cleaning up
    resources used for that connection. The network connection may still be valid.
    """

    NM_DEVICE_STATE_FAILED = 120
    """
    The device failed to connect to the requested network and is cleaning up the connection request
    """


@unique
class NMDeviceType(IntEnum):
    """
    NMDeviceType values indicate the type of hardware represented by a device object.
    """

    NM_DEVICE_TYPE_UNKNOWN = 0
    """
    Unknown device
    """

    NM_DEVICE_TYPE_ETHERNET = 1
    """
    A wired ethernet device
    """

    NM_DEVICE_TYPE_WIFI = 2
    """
    An 802.11 Wi-Fi device
    """

    NM_DEVICE_TYPE_UNUSED1 = 3
    """
    Not used
    """

    NM_DEVICE_TYPE_UNUSED2 = 4
    """
    Not used
    """

    NM_DEVICE_TYPE_BT = 5
    """
    A Bluetooth device supporting PAN or DUN access protocols
    """

    NM_DEVICE_TYPE_OLPC_MESH = 6
    """
    An OLPC XO mesh networking device
    """

    NM_DEVICE_TYPE_WIMAX = 7
    """
    An 802.16e Mobile WiMAX broadband device
    """

    NM_DEVICE_TYPE_MODEM = 8
    """
    A modem supporting analog telephone, CDMA/EVDO, GSM/UMTS, or LTE network access protocols
    """

    NM_DEVICE_TYPE_INFINIBAND = 9
    """
    An IP-over-InfiniBand device
    """

    NM_DEVICE_TYPE_BOND = 10
    """
    A bond master interface
    """

    NM_DEVICE_TYPE_VLAN = 11
    """
    An 802.1Q VLAN interface
    """

    NM_DEVICE_TYPE_ADSL = 12
    """
    ADSL modem
    """

    NM_DEVICE_TYPE_BRIDGE = 13
    """
    A bridge master interface
    """

    NM_DEVICE_TYPE_GENERIC = 14
    """
    Generic support for unrecognized device types
    """

    NM_DEVICE_TYPE_TEAM = 15
    """
    A team master interface
    """

    NM_DEVICE_TYPE_TUN = 16
    """
    A TUN or TAP interface
    """

    NM_DEVICE_TYPE_IP_TUNNEL = 17
    """
    A IP tunnel interface
    """

    NM_DEVICE_TYPE_MACVLAN = 18
    """
    A MACVLAN interface
    """

    NM_DEVICE_TYPE_VXLAN = 19
    """
    A VXLAN interface
    """

    NM_DEVICE_TYPE_VETH = 20
    """
    A VETH interface
    """

    NM_DEVICE_TYPE_MACSEC = 21
    """
    A MACsec interface
    """

    NM_DEVICE_TYPE_DUMMY = 22
    """
    A dummy interface
    """

    NM_DEVICE_TYPE_PPP = 23
    """
    A PPP interface
    """

    NM_DEVICE_TYPE_OVS_INTERFACE = 24
    """
    A Open vSwitch interface
    """

    NM_DEVICE_TYPE_OVS_PORT = 25
    """
    A Open vSwitch port
    """

    NM_DEVICE_TYPE_OVS_BRIDGE = 26
    """
    A Open vSwitch bridge
    """

    NM_DEVICE_TYPE_WPAN = 27
    """
    A IEEE 802.15.4 (WPAN) MAC Layer Device
    """

    NM_DEVICE_TYPE_6LOWPAN = 28
    """
    6LoWPAN interface
    """

    NM_DEVICE_TYPE_WIREGUARD = 29
    """
    A WireGuard interface
    """

    NM_DEVICE_TYPE_WIFI_P2P = 30
    """
    An 802.11 Wi-Fi P2P device. Since: 1.16.
    """

    NM_DEVICE_TYPE_VRF = 31
    """
    A VRF (Virtual Routing and Forwarding) interface. Since: 1.24.
    """

    NM_DEVICE_TYPE_LOOPBACK = 32
    """
    A loopback interface. Since: 1.42.
    """


@unique
class NMActiveConnectionState(IntEnum):
    """
    NMActiveConnectionState values indicate the state of a connection to a specific network while it
    is starting, connected, or disconnecting from that network.
    """

    NM_ACTIVE_CONNECTION_STATE_UNKNOWN = 0
    """
    The state of the connection is unknown
    """

    NM_ACTIVE_CONNECTION_STATE_ACTIVATING = 1
    """
    A network connection is being prepared
    """

    NM_ACTIVE_CONNECTION_STATE_ACTIVATED = 2
    """
    There is a connection to the network
    """

    NM_ACTIVE_CONNECTION_STATE_DEACTIVATING = 3
    """
    The network connection is being torn down and cleaned up
    """

    NM_ACTIVE_CONNECTION_STATE_DEACTIVATED = 4
    """
    The network connection is disconnected and will be removed
    """


@unique
class NMSettingSecretFlags(IntFlag):
    """
    These flags indicate specific behavior related to handling of a secret. Each secret has a
    corresponding set of these flags which indicate how the secret is to be stored and/or requested
    when it is needed.
    """

    NM_SETTING_SECRET_FLAG_NONE = 0x00000000
    """
    The system is responsible for providing and storing this secret (default)
    """

    NM_SETTING_SECRET_FLAG_AGENT_OWNED = 0x00000001
    """
    A user secret agent is responsible for providing and storing this secret; when it is required
    agents will be asked to retrieve it
    """

    NM_SETTING_SECRET_FLAG_NOT_SAVED = 0x00000002
    """
    This secret should not be saved, but should be requested from the user each time it is needed
    """

    NM_SETTING_SECRET_FLAG_NOT_REQUIRED = 0x00000004
    """
    In situations where it cannot be automatically determined that the secret is required (some VPNs
    and PPP providers don't require all secrets) this flag indicates that the specific secret is not
    required
    """


@unique
class NMSettingConnectionAutoconnectSlaves(IntEnum):
    """
    NMSettingConnectionAutoconnectSlaves values indicate whether slave connections should be
    activated when master is activated.
    """

    NM_SETTING_CONNECTION_AUTOCONNECT_SLAVES_DEFAULT = -1
    """
    Default value
    """

    NM_SETTING_CONNECTION_AUTOCONNECT_SLAVES_NO = 0
    """
    Slaves are not brought up when master is activated
    """

    NM_SETTING_CONNECTION_AUTOCONNECT_SLAVES_YES = 1
    """
    Slaves are brought up when master is activated
    """


@unique
class NMMetered(IntEnum):
    """
    The NMMetered enum has two different purposes: one is to configure "connection.metered" setting
    of a connection profile in NMSettingConnection, and the other is to express the actual metered
    state of the NMDevice at a given moment.

    For the connection profile only NM_METERED_UNKNOWN, NM_METERED_NO and NM_METERED_YES are
    allowed.

    The device's metered state at runtime is determined by the profile which is currently active. If
    the profile explicitly specifies NM_METERED_NO or NM_METERED_YES, then the device's metered
    state is as such. If the connection profile leaves it undecided at NM_METERED_UNKNOWN (the
    default), then NetworkManager tries to guess the metered state, for example based on the device
    type or on DHCP options (like Android devices exposing a "ANDROID_METERED" DHCP vendor option).
    This then leads to either NM_METERED_GUESS_NO or NM_METERED_GUESS_YES.

    Most applications probably should treat the runtime state NM_METERED_GUESS_YES like
    NM_METERED_YES, and all other states as not metered.

    Note that the per-device metered states are then combined to a global metered state. This is
    basically the metered state of the device with the best default route. However, that
    generalization of a global metered state may not be correct if the default routes for IPv4 and
    IPv6 are on different devices, or if policy routing is configured. In general, the global
    metered state tries to express whether the traffic is likely metered, but since that depends on
    the traffic itself, there is not one answer in all cases. Hence, an application may want to
    consider the per-device's metered states.

    Since: 1.2
    """

    NM_METERED_UNKNOWN = 0
    """
    The metered status is unknown
    """

    NM_METERED_YES = 1
    """
    Metered, the value was explicitly configured
    """

    NM_METERED_NO = 2
    """
    Not metered, the value was explicitly configured
    """

    NM_METERED_GUESS_YES = 3
    """
    Metered, the value was guessed
    """

    NM_METERED_GUESS_NO = 4
    """
    Not metered, the value was guessed
    """


@unique
class NMSettingIP6ConfigPrivacy(IntEnum):
    """
    NMSettingIP6ConfigPrivacy values indicate if and how IPv6 Privacy Extensions are used (RFC4941).
    """

    NM_SETTING_IP6_CONFIG_PRIVACY_UNKNOWN = -1
    """
    Unknown or no value specified
    """

    NM_SETTING_IP6_CONFIG_PRIVACY_DISABLED = 0
    """
    IPv6 Privacy Extensions are disabled
    """

    NM_SETTING_IP6_CONFIG_PRIVACY_PREFER_PUBLIC_ADDR = 1
    """
    IPv6 Privacy Extensions are enabled, but public addresses are preferred over temporary addresses
    """

    NM_SETTING_IP6_CONFIG_PRIVACY_PREFER_TEMP_ADDR = 2
    """
    IPv6 Privacy Extensions are enabled and temporary addresses are preferred over public addresses
    """


@unique
class NMSettingIP6ConfigAddrGenMode(IntEnum):
    """
    NMSettingIP6ConfigAddrGenMode controls how the Interface Identifier for RFC4862 Stateless
    Address Autoconfiguration is created.
    """

    NM_SETTING_IP6_CONFIG_ADDR_GEN_MODE_EUI64 = 0
    """
    The Interface Identifier is derived from the interface hardware address.
    """

    NM_SETTING_IP6_CONFIG_ADDR_GEN_MODE_STABLE_PRIVACY = 1
    """
    The Interface Identifier is created by using a cryptographically secure hash of a secret
    host-specific key along with the connection identification and the network address as specified
    by RFC7217.
    """

    NM_SETTING_IP6_CONFIG_ADDR_GEN_MODE_DEFAULT_OR_EUI64 = 2
    """
    Fallback to the global default, and if unspecified use "eui64". Since: 1.40.
    """

    NM_SETTING_IP6_CONFIG_ADDR_GEN_MODE_DEFAULT = 3
    """
    Fallback to the global default, and if unspecified use "stable-privacy". Since: 1.40.
    """


@unique
class NMTernary(IntEnum):
    """
    A boolean value that can be overridden by a default.

    Since: 1.14
    """

    NM_TERNARY_DEFAULT = -1
    """
    Use the globally-configured default value.
    """

    NM_TERNARY_FALSE = 0
    """
    The option is disabled.
    """

    NM_TERNARY_TRUE = 1
    """
    The option is enabled.
    """


class NMWepKeyType(IntEnum):
    """
    The NMWepKeyType values specify how any WEP keys present in the setting are interpreted. There
    are no standards governing how to hash the various WEP key/passphrase formats into the actual
    WEP key. Unfortunately some WEP keys can be interpreted in multiple ways, requiring the setting
    to specify how to interpret the any WEP keys. For example, the key "732f2d712e4a394a375d366931"
    is both a valid Hexadecimal WEP key and a WEP passphrase. Further, many ASCII keys are also
    valid WEP passphrases, but since passphrases and ASCII keys are hashed differently to determine
    the actual WEP key the type must be specified.
    """

    NM_WEP_KEY_TYPE_UNKNOWN = 0
    """
    Unknown WEP key type
    """

    NM_WEP_KEY_TYPE_KEY = 1
    """
    Indicates a hexadecimal or ASCII formatted WEP key. Hex keys are either 10 or 26 hexadecimal
    characters (ie "5f782f2f5f" or "732f2d712e4a394a375d366931"), while ASCII keys are either 5 or
    13 ASCII characters (ie "abcde" or "blahblah99$*1").
    """

    NM_WEP_KEY_TYPE_PASSPHRASE = 2
    """
    Indicates a WEP passphrase (ex "I bought a duck on my way back from the market 235Q&^%^*%")
    instead of a hexadecimal or ASCII key. Passphrases are between 8 and 64 characters inclusive and
    are hashed the actual WEP key using the MD5 hash algorithm.
    """

    NM_WEP_KEY_TYPE_LAST = NM_WEP_KEY_TYPE_PASSPHRASE
    """
    Placeholder value for bounds-checking
    """


NM_SETTING_CONNECTION_DEFAULTS: Dict[str, Any] = {
    "auth-retries": -1,
    "autoconnect": True,
    "autoconnect-priority": 0,
    "autoconnect-retries": -1,
    "autoconnect-slaves": NMSettingConnectionAutoconnectSlaves.NM_SETTING_CONNECTION_AUTOCONNECT_SLAVES_DEFAULT,
    "dns-over-tls": -1,
    "gateway-ping-timeout": 0,
    "id": None,
    "interface-name": None,
    "lldp": -1,
    "llmnr": -1,
    "master": None,
    "mdns": -1,
    "metered": NMMetered.NM_METERED_UNKNOWN,
    "mptcp-flags": 0,
    "mud-url": None,
    "multi-connect": 0,
    "permissions": [],
    "read-only": False,
    "secondaries": [],
    "slave-type": None,
    "stable-id": None,
    "timestamp": 0,
    "type": None,
    "uuid": None,
    "wait-activation-delay": -1,
    "wait-device-timeout": -1,
    "zone": None,
}
"""
Default values for the NM.SettingConnection settings. Values taken from:
https://lazka.github.io/pgi-docs/#NM-1.0/classes/SettingConnection.html
"""


NM_SETTING_IPCONFIG_DEFAULTS: Dict[str, Any] = {
    "addresses": None,
    "auto-route-ext-gw": NMTernary.NM_TERNARY_DEFAULT,
    "dad-timeout": -1,
    "dhcp-hostname": None,
    "dhcp-hostname-flags": 0,
    "dhcp-iaid": None,
    "dhcp-reject-servers": [],
    "dhcp-send-hostname": True,
    "dhcp-timeout": 0,
    "dns": [],
    "dns-options": [],
    "dns-priority": 0,
    "dns-search": [],
    "gateway": None,
    "ignore-auto-dns": False,
    "ignore-auto-routes": False,
    "may-fail": True,
    "method": None,
    "never-default": False,
    "required-timeout": -1,
    "route-metric": -1,
    "route-table": 0,
    "routes": None,
}
"""
Default values for the NM.SettingIPConfig settings. Values taken from:
https://lazka.github.io/pgi-docs/#NM-1.0/classes/SettingIPConfig.html
"""


NM_SETTING_IP4CONFIG_DEFAULTS: Dict[str, Any] = {
    **NM_SETTING_IPCONFIG_DEFAULTS,
    "dhcp-client-id": None,
    "dhcp-fqdn": None,
    "dhcp-vendor-class-identifier": None,
    "link-local": 0,
}
"""
Default values for the NM.SettingIP4Config settings. Values taken from:
https://lazka.github.io/pgi-docs/#NM-1.0/classes/SettingIP4Config.html
"""


NM_SETTING_IP6CONFIG_DEFAULTS: Dict[str, Any] = {
    **NM_SETTING_IPCONFIG_DEFAULTS,
    "addr-gen-mode": NMSettingIP6ConfigAddrGenMode.NM_SETTING_IP6_CONFIG_ADDR_GEN_MODE_DEFAULT,
    "dhcp-duid": None,
    "ip6-privacy": NMSettingIP6ConfigPrivacy.NM_SETTING_IP6_CONFIG_PRIVACY_UNKNOWN,
    "mtu": 0,
    "ra-timeout": 0,
    "token": None,
}
"""
Default values for the NM.SettingIP6Config settings. Values taken from:
https://lazka.github.io/pgi-docs/#NM-1.0/classes/SettingIP6Config.html
"""


NM_SETTING_PROXY_DEFAULTS: Dict[str, Any] = {
    "browser-only": False,
    "method": 0,
    "pac-script": None,
    "pac-url": None,
}
"""
Default values for the NM.SettingProxy settings. Values taken from:
https://lazka.github.io/pgi-docs/#NM-1.0/classes/SettingProxy.html
"""


NM_SETTING_WIRED_DEFAULTS: Dict[str, Any] = {
    "accept-all-mac-addresses": NMTernary.NM_TERNARY_DEFAULT,
    "auto-negotiate": False,
    "cloned-mac-address": None,
    "duplex": None,
    "generate-mac-address-mask": None,
    "mac-address": None,
    "mac-address-blacklist": [],
    "mtu": 0,
    "port": None,
    "s390-nettype": None,
    "s390-options": None,
    "s390-subchannels": [],
    "speed": 0,
    "wake-on-lan": 1,
    "wake-on-lan-password": None,
}
"""
Default values for the NM.SettingWired settings. Values taken from:
https://lazka.github.io/pgi-docs/#NM-1.0/classes/SettingWired.html
"""


NM_SETTING_WIRELESS_DEFAULTS: Dict[str, Any] = {
    "ap-isolation": NMTernary.NM_TERNARY_DEFAULT,
    "band": None,
    "bssid": None,
    "channel": 0,
    "cloned-mac-address": None,
    "generate-mac-address-mask": None,
    "hidden": False,
    "mac-address": None,
    "mac-address-blacklist": [],
    "mac-address-randomization": 0,
    "mode": None,
    "mtu": 0,
    "powersave": 0,
    "rate": 0,
    "seen-bssids": [],
    "ssid": None,
    "tx-power": 0,
    "wake-on-wlan": 1,
}
"""
Default values for the NM.SettingWireless settings. Values taken from:
https://lazka.github.io/pgi-docs/#NM-1.0/classes/SettingWireless.html
"""


NM_SETTING_WIRELESS_SECURITY_DEFAULTS: Dict[str, Any] = {
    "auth-alg": None,
    "fils": 0,
    "group": [],
    "key-mgmt": None,
    "leap-password": None,
    "leap-password-flags": NMSettingSecretFlags.NM_SETTING_SECRET_FLAG_NONE,
    "leap-username": None,
    "pairwise": [],
    "pmf": 0,
    "proto": [],
    "psk": None,
    "psk-flags": NMSettingSecretFlags.NM_SETTING_SECRET_FLAG_NONE,
    "wep-key0": None,
    "wep-key1": None,
    "wep-key2": None,
    "wep-key3": None,
    "wep-key-flags": NMSettingSecretFlags.NM_SETTING_SECRET_FLAG_NONE,
    "wep-key-type": NMWepKeyType.NM_WEP_KEY_TYPE_UNKNOWN,
    "wep-tx-keyidx": 0,
    "wps-method": 0,
}
"""
Default values for the NM.SettingWirelessSecurity settings. Values taken from:
https://lazka.github.io/pgi-docs/#NM-1.0/classes/SettingWirelessSecurity.html
"""


NM_SETTING_8021X_DEFAULTS: Dict[str, Any] = {
    "altsubject-matches": [],
    "anonymous-identity": None,
    "auth-timeout": 0,
    "ca-cert": None,
    "ca-cert-password": None,
    "ca-cert-password-flags": NMSettingSecretFlags.NM_SETTING_SECRET_FLAG_NONE,
    "ca-path": None,
    "client-cert": None,
    "client-cert-password": None,
    "client-cert-password-flags": NMSettingSecretFlags.NM_SETTING_SECRET_FLAG_NONE,
    "domain-match": None,
    "domain-suffix-match": None,
    "eap": [],
    "identity": None,
    "optional": False,
    "pac-file": None,
    "password": None,
    "password-flags": NMSettingSecretFlags.NM_SETTING_SECRET_FLAG_NONE,
    "password-raw": None,
    "password-raw-flags": NMSettingSecretFlags.NM_SETTING_SECRET_FLAG_NONE,
    "phase1-auth-flags": 0,
    "phase1-fast-provisioning": None,
    "phase1-peaplabel": None,
    "phase1-peapver": None,
    "phase2-altsubject-matches": [],
    "phase2-auth": None,
    "phase2-autheap": None,
    "phase2-ca-cert": None,
    "phase2-ca-cert-password": None,
    "phase2-ca-cert-password-flags": NMSettingSecretFlags.NM_SETTING_SECRET_FLAG_NONE,
    "phase2-ca-path": None,
    "phase2-client-cert": None,
    "phase2-client-cert-password": None,
    "phase2-client-cert-password-flags": NMSettingSecretFlags.NM_SETTING_SECRET_FLAG_NONE,
    "phase2-domain-match": None,
    "phase2-domain-suffix-match": None,
    "phase2-private-key": None,
    "phase2-private-key-password": None,
    "phase2-private-key-password-flags": NMSettingSecretFlags.NM_SETTING_SECRET_FLAG_NONE,
    "phase2-subject-match": None,
    "pin": None,
    "pin-flags": NMSettingSecretFlags.NM_SETTING_SECRET_FLAG_NONE,
    "private-key": None,
    "private-key-password": None,
    "private-key-password-flags": NMSettingSecretFlags.NM_SETTING_SECRET_FLAG_NONE,
    "subject-match": None,
    "system-ca-certs": False,
}
"""
Default values for the NM.Setting8021x settings. Values taken from:
https://lazka.github.io/pgi-docs/#NM-1.0/classes/Setting8021x.html
"""

DBUS_FAST_TYPE_CONVERSION: Dict[type, str] = {
    bool: "b",
    int: "i",
    float: "d",
    str: "s",
    list: "ay",
    dict: "v",
    bytearray: "ay",
}
"""
Dictionary used to convert from a Python type to the proper DBus token signature.
"""


class NetworkManagerService(object, metaclass=Singleton):
    DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"

    NM_INTROSPECTION_INTERFACES_DIR = "/usr/share/dbus-1/interfaces"

    NM_BUS_NAME = "org.freedesktop.NetworkManager"

    NM_CONNECTION_MANAGER_OBJ_PATH = "/org/freedesktop/NetworkManager"
    NM_CONNECTION_MANAGER_IFACE = "org.freedesktop.NetworkManager"

    NM_DEVICE_OBJ_PATH = "/org/freedesktop/NetworkManager/Device"
    NM_DEVICE_IFACE = "org.freedesktop.NetworkManager.Device"
    NM_DEVICE_WIRED_IFACE = "org.freedesktop.NetworkManager.Device.Wired"
    NM_DEVICE_WIRELESS_IFACE = "org.freedesktop.NetworkManager.Device.Wireless"

    NM_SETTINGS_OBJ_PATH = "/org/freedesktop/NetworkManager/Settings"
    NM_SETTINGS_IFACE = "org.freedesktop.NetworkManager.Settings"
    NM_SETTINGS_CONNECTION_IFACE = "org.freedesktop.NetworkManager.Settings.Connection"

    NM_CONNECTION_ACTIVE_OBJ_PATH = "/org/freedesktop/NetworkManager/ActiveConnection"
    NM_CONNECTION_ACTIVE_IFACE = "org.freedesktop.NetworkManager.Connection.Active"

    NM_IP4CONFIG_IFACE = "org.freedesktop.NetworkManager.IP4Config"
    NM_IP6CONFIG_IFACE = "org.freedesktop.NetworkManager.IP6Config"

    NM_DHCP4CONFIG_IFACE = "org.freedesktop.NetworkManager.DHCP4Config"
    NM_DHCP6CONFIG_IFACE = "org.freedesktop.NetworkManager.DHCP6Config"

    NM_ACCESS_POINT_IFACE = "org.freedesktop.NetworkManager.AccessPoint"

    async def get_all_devices(self) -> List[str]:
        bus = await DBusManager().get_bus()

        reply = await bus.call(
            Message(
                destination=self.NM_BUS_NAME,
                path=self.NM_CONNECTION_MANAGER_OBJ_PATH,
                interface=self.NM_CONNECTION_MANAGER_IFACE,
                member="GetAllDevices",
            )
        )

        if reply.message_type == MessageType.ERROR:
            raise Exception(reply.body[0])

        if not isinstance(reply.body[0], list):
            raise Exception("Invalid return type")

        return reply.body[0]

    async def activate_connection(
        self, connection: str, device: str, specific_object: str
    ) -> str:
        bus = await DBusManager().get_bus()

        reply = await bus.call(
            Message(
                destination=self.NM_BUS_NAME,
                path=self.NM_CONNECTION_MANAGER_OBJ_PATH,
                interface=self.NM_CONNECTION_MANAGER_IFACE,
                member="ActivateConnection",
                signature="ooo",
                body=[connection, device, specific_object],
            )
        )

        if reply.message_type == MessageType.ERROR:
            raise Exception(reply.body[0])

        return reply.body[0]

    async def deactivate_connection(self, active_connection: str) -> None:
        bus = await DBusManager().get_bus()

        reply = await bus.call(
            Message(
                destination=self.NM_BUS_NAME,
                path=self.NM_CONNECTION_MANAGER_OBJ_PATH,
                interface=self.NM_CONNECTION_MANAGER_IFACE,
                member="DeactivateConnection",
                signature="o",
                body=[active_connection],
            )
        )

        if reply.message_type == MessageType.ERROR:
            raise Exception(reply.body[0])

    async def wifi_device_request_scan(self, dev_obj_path: str, options: dict) -> None:
        bus = await DBusManager().get_bus()

        reply = await bus.call(
            Message(
                destination=self.NM_BUS_NAME,
                path=dev_obj_path,
                interface=self.NM_DEVICE_WIRELESS_IFACE,
                member="RequestScan",
                signature="a{sv}",
                body=[options],
            )
        )

        if reply.message_type == MessageType.ERROR:
            raise Exception(reply.body[0])

    async def get_connection_settings(self, connection_obj_path: str) -> dict:
        bus = await DBusManager().get_bus()

        reply = await bus.call(
            Message(
                destination=self.NM_BUS_NAME,
                path=connection_obj_path,
                interface=self.NM_SETTINGS_CONNECTION_IFACE,
                member="GetSettings",
            )
        )

        if reply.message_type == MessageType.ERROR:
            raise Exception(reply.body[0])

        result = reply.body[0]

        return result

    async def delete_connection(self, connection_obj_path: str) -> None:
        bus = await DBusManager().get_bus()

        reply = await bus.call(
            Message(
                destination=self.NM_BUS_NAME,
                path=connection_obj_path,
                interface=self.NM_SETTINGS_CONNECTION_IFACE,
                member="Delete",
            )
        )

        if reply.message_type == MessageType.ERROR:
            raise Exception(reply.body[0])

    async def get_connection_obj_path_by_uuid(self, uuid: str) -> str:
        bus = await DBusManager().get_bus()

        reply = await bus.call(
            Message(
                destination=self.NM_BUS_NAME,
                path=self.NM_SETTINGS_OBJ_PATH,
                interface=self.NM_SETTINGS_IFACE,
                member="GetConnectionByUuid",
                signature="s",
                body=[uuid],
            )
        )

        if reply.message_type == MessageType.ERROR:
            raise Exception(reply.body[0])

        result = reply.body[0]

        return result

    async def add_connection(self, connection: dict) -> str:
        bus = await DBusManager().get_bus()

        reply = await bus.call(
            Message(
                destination=self.NM_BUS_NAME,
                path=self.NM_SETTINGS_OBJ_PATH,
                interface=self.NM_SETTINGS_IFACE,
                member="AddConnection",
                signature="a{sa{sv}}",
                body=[connection],
            )
        )

        if reply.message_type == MessageType.ERROR:
            raise Exception(reply.body[0])

        result = reply.body[0]

        return result

    async def update_connection(
        self, connection_obj_path: str, connection: dict
    ) -> None:
        """
        Update the connection at the provided object path ('connection_obj_path') with the new
        settings defined in the dictionary 'connection' using the NetworkManager D-Bus API.

        https://people.freedesktop.org/~lkundrak/nm-docs/gdbus-org.freedesktop.NetworkManager.Settings.Connection.html#gdbus-method-org-freedesktop-NetworkManager-Settings-Connection.Update
        """
        bus = await DBusManager().get_bus()

        reply = await bus.call(
            Message(
                destination=self.NM_BUS_NAME,
                path=connection_obj_path,
                interface=self.NM_SETTINGS_CONNECTION_IFACE,
                member="Update",
                signature="a{sa{sv}}",
                body=[connection],
            )
        )

        if reply.message_type == MessageType.ERROR:
            raise Exception(reply.body[0])

    async def get_obj_properties(self, obj_path: str, interface: str) -> dict:
        bus = await DBusManager().get_bus()

        reply = await bus.call(
            Message(
                destination=self.NM_BUS_NAME,
                path=obj_path,
                interface=self.DBUS_PROP_IFACE,
                member="GetAll",
                signature="s",
                body=[interface],
            )
        )

        if reply.message_type == MessageType.ERROR:
            raise Exception(reply.body[0])

        result = reply.body[0]
        for key in result.keys():
            result[key] = result[key].value

        return result

    async def set_obj_properties(
        self,
        obj_path: str,
        interface: str,
        property_name: str,
        value: Any,
        value_signature: str,
    ) -> None:
        bus = await DBusManager().get_bus()

        reply = await bus.call(
            Message(
                destination=self.NM_BUS_NAME,
                path=obj_path,
                interface=self.DBUS_PROP_IFACE,
                member="Set",
                signature="ssv",
                body=[interface, property_name, Variant(value_signature, value)],
            )
        )

        if reply.message_type == MessageType.ERROR:
            raise Exception(reply.body[0])

    async def prepare_setting(
        self, setting_name: str, connection: dict, new_connection: dict
    ) -> None:
        for key in connection[setting_name]:
            new_connection[setting_name][key] = Variant(
                DBUS_FAST_TYPE_CONVERSION[type(connection[setting_name][key])],
                connection[setting_name][key],
            )

    async def convert_cert_to_nm_path_scheme(self, cert_name: str) -> bytearray:
        """
        For certain certs, NM supports specifying the path to the cert prefixed with "file://"
        and NUL terminated
        """
        return bytearray(
            str(
                "file://{0}{1}\x00".format(
                    summit_rcm.definition.FILEDIR_DICT.get("cert"), cert_name
                )
            ),
            "utf-8",
        )

    async def prepare_new_connection_data(self, connection: dict) -> dict:
        new_connection = {}

        if connection.get("connection"):
            new_connection["connection"] = {}
            await self.prepare_setting("connection", connection, new_connection)

        if connection.get("802-11-wireless"):
            new_connection["802-11-wireless"] = {}
            await self.prepare_setting("802-11-wireless", connection, new_connection)

            # Handle the special case of the 'ssid' property, if present
            ssid = connection["802-11-wireless"].get("ssid", None)
            if ssid is not None:
                new_connection["802-11-wireless"]["ssid"] = Variant(
                    "ay", bytearray(ssid, "utf-8")
                )

            # if 'mode' is not provided, assume 'infrastructure'
            if not connection["802-11-wireless"].get("mode", None):
                new_connection["802-11-wireless"]["mode"] = Variant(
                    "s", "infrastructure"
                )

        if connection.get("802-11-wireless-security"):
            new_connection["802-11-wireless-security"] = {}

            # NetworkManager expects some 802-11-wireless-security properties to be an array of
            # strings
            for key in ["pairwise", "group", "proto"]:
                if connection["802-11-wireless-security"].get(key):
                    if not isinstance(
                        connection["802-11-wireless-security"][key], list
                    ):
                        connection["802-11-wireless-security"][key] = [
                            str(connection["802-11-wireless-security"][key])
                        ]

                    new_connection["802-11-wireless-security"][key] = Variant(
                        "as", connection["802-11-wireless-security"][key]
                    )

                    del connection["802-11-wireless-security"][key]

            await self.prepare_setting(
                "802-11-wireless-security", connection, new_connection
            )

        if connection.get("802-1x"):
            new_connection["802-1x"] = {}

            # NetworkManager expects some 802-1x properties to be an array of strings
            for key in [
                "eap",
                "phase2-auth",
                "phase2-autheap",
                "altsubject-matches",
                "phase2-altsubject-matches",
            ]:
                if connection["802-1x"].get(key):
                    if not isinstance(connection["802-1x"][key], list):
                        connection["802-1x"][key] = [str(connection["802-1x"][key])]

                    new_connection["802-1x"][key] = Variant(
                        "as", connection["802-1x"][key]
                    )

                    del connection["802-1x"][key]

            for cert in [
                "ca-cert",
                "client-cert",
                "private-key",
                "phase2-ca-cert",
                "phase2-client-cert",
                "phase2-private-key",
            ]:
                if connection["802-1x"].get(cert):
                    connection["802-1x"][cert] = (
                        await self.convert_cert_to_nm_path_scheme(
                            connection["802-1x"][cert]
                        )
                    )

            if connection["802-1x"].get("pac-file"):
                # pac-file parameter provided, prepend path to certs
                connection["802-1x"][
                    "pac-file"
                ] = f"{summit_rcm.definition.FILEDIR_DICT.get('pac')}{connection['802-1x']['pac-file']}"

            await self.prepare_setting("802-1x", connection, new_connection)

        if connection.get("gsm"):
            new_connection["gsm"] = {}

            await self.prepare_setting("gsm", connection, new_connection)

        if connection.get("ipv4"):
            new_connection["ipv4"] = {}

            if connection["ipv4"].get("address-data"):
                # Found the 'address-data' property - this isn't technically the proper property
                # name to use here (should be 'addresses'), but this is what was used in the past,
                # so we need to support it.
                #
                # The NetworkManager DBus API documentation describes the expected format of the
                # 'Addresses' property as:
                #
                # Array of arrays of IPv4 address/prefix/gateway. All 3 elements of each array are
                # in network byte order.
                # Essentially: [(addr, prefix, gateway), (addr, prefix, gateway), ...]
                #
                # See below for more info:
                # https://people.freedesktop.org/~lkundrak/nm-docs/gdbus-org.freedesktop.NetworkManager.IP4Config.html
                new_connection["ipv4"]["addresses"] = Variant(
                    "aau",
                    [
                        [
                            int.from_bytes(
                                inet_pton(AF_INET, address["address"]), byteorder
                            ),
                            int(address["prefix"]),
                            (
                                int.from_bytes(
                                    inet_pton(AF_INET, connection["ipv4"]["gateway"]),
                                    byteorder,
                                )
                                if connection["ipv4"].get("gateway", None) is not None
                                else 0
                            ),
                        ]
                        for address in connection["ipv4"]["address-data"]
                    ],
                )
                del connection["ipv4"]["address-data"]

            if connection["ipv4"].get("dns"):
                new_connection["ipv4"]["dns"] = Variant(
                    "au",
                    [
                        int.from_bytes(inet_pton(AF_INET, nameserver), byteorder)
                        for nameserver in connection["ipv4"]["dns"]
                    ],
                )
                del connection["ipv4"]["dns"]

            await self.prepare_setting("ipv4", connection, new_connection)

        if connection.get("ipv6"):
            new_connection["ipv6"] = {}

            if connection["ipv6"].get("address-data"):
                # Found the 'address-data' property - this isn't technically the proper property
                # name to use here (should be 'addresses'), but this is what was used in the past,
                # so we need to support it.
                #
                # The NetworkManager DBus API documentation describes the expected format of the
                # 'Addresses' property as:
                #
                # Array of tuples of IPv6 address/prefix/gateway.
                #
                # See below for more info:
                # https://people.freedesktop.org/~lkundrak/nm-docs/gdbus-org.freedesktop.NetworkManager.IP6Config.html
                new_connection["ipv6"]["addresses"] = Variant(
                    "a(ayuay)",
                    [
                        [
                            inet_pton(AF_INET6, address["address"]),
                            int(address["prefix"]),
                            (
                                inet_pton(AF_INET6, connection["ipv6"]["gateway"])
                                if connection["ipv6"].get("gateway", None) is not None
                                else bytes(0)
                            ),
                        ]
                        for address in connection["ipv6"]["address-data"]
                    ],
                )
                del connection["ipv6"]["address-data"]

            if connection["ipv6"].get("dns"):
                new_connection["ipv6"]["dns"] = Variant(
                    "aay",
                    [
                        inet_pton(AF_INET6, nameserver)
                        for nameserver in connection["ipv6"]["dns"]
                    ],
                )
                del connection["ipv6"]["dns"]

            await self.prepare_setting("ipv6", connection, new_connection)

        return new_connection

    async def reload_connections(self) -> bool:
        """
        Trigger NetworkManager to reload all connection files from disk, including noticing any
        added or deleted connection files.
        """
        bus = await DBusManager().get_bus()

        reply = await bus.call(
            Message(
                destination=self.NM_BUS_NAME,
                path=self.NM_SETTINGS_OBJ_PATH,
                interface=self.NM_SETTINGS_IFACE,
                member="ReloadConnections",
            )
        )

        if reply.message_type == MessageType.ERROR:
            raise Exception(reply.body[0])

        return bool(reply.body[0])
