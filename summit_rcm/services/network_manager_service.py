#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
from asyncio import wait_for, Lock
from socket import inet_pton, inet_ntop, AF_INET, AF_INET6
from sys import byteorder
from syslog import LOG_ERR, syslog
from typing import Any, Dict, List, Optional, Tuple
from enum import IntFlag, IntEnum, unique
import os

try:
    from dbus_fast import Message, MessageType, Variant
    from dbus_fast.aio.proxy_object import ProxyInterface, ProxyObject
    from dbus_fast.errors import InterfaceNotFoundError
    from summit_rcm.dbus_manager import DBusManager
    from pyroute2.iwutil import IW
    from pyroute2.netlink import NLM_F_REQUEST, NLM_F_DUMP
    from pyroute2.netlink.nl80211 import nl80211cmd, NL80211_NAMES
except ImportError as error:
    # Ignore the error if the dbus_fast module is not available if generating documentation
    if os.environ.get("DOCS_GENERATION") != "True":
        raise error

    class nl80211cmd:
        """Dummy nl80211cmd class for documentation generation"""

        class STAInfo:
            """Dummy STAInfo class for documentation generation"""

            class rate_info:
                """Dummy rate_info class for documentation generation"""

            class bss_param:
                """Dummy bss_param class for documentation generation"""

    Message = None
    MessageType = None
    Variant = None
    ProxyInterface = None
    ProxyObject = None
    InterfaceNotFoundError = None

from summit_rcm.definition import FILEDIR_DICT, INVALID_RSSI
from summit_rcm.utils import (
    Singleton,
    frequency_to_channel,
    variant_to_python,
    to_camel_case,
)
from summit_rcm.services.network_manager_systemd_service import (
    NetworkManagerSystemdService,
)


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

    NM_DEVICE_STATE_REASON_DEVICE_HANDLER_FAILED = 68
    """
    The device handler dispatcher returned an error. Since: 1.46
    """

    NM_DEVICE_STATE_REASON_UNMANAGED_BY_DEFAULT = 69
    """
    The device is unmanaged because the device type is unmanaged by default. Since: 1.48
    """

    NM_DEVICE_STATE_REASON_UNMANAGED_EXTERNAL_DOWN = 70
    """
    The device is unmanaged because it is an external device and is unconfigured (down or without
    addresses). Since: 1.48
    """

    NM_DEVICE_STATE_REASON_UNMANAGED_LINK_NOT_INIT = 71
    """
    The device is unmanaged because the link is not initialized by udev. Since: 1.48
    """

    NM_DEVICE_STATE_REASON_UNMANAGED_QUITTING = 72
    """
    The device is unmanaged because NetworkManager is quitting. Since: 1.48
    """

    NM_DEVICE_STATE_REASON_UNMANAGED_SLEEPING = 73
    """
    The device is unmanaged because networking is disabled or the system is suspended. Since: 1.48
    """

    NM_DEVICE_STATE_REASON_UNMANAGED_USER_CONF = 74
    """
    The device is unmanaged by user decision in NetworkManager.conf ('unmanaged' in a [device*]
    section). Since: 1.48
    """

    NM_DEVICE_STATE_REASON_UNMANAGED_USER_EXPLICIT = 75
    """
    The device is unmanaged by explicit user decision (e.g. 'nmcli device set $DEV managed no').
    Since: 1.48
    """

    NM_DEVICE_STATE_REASON_UNMANAGED_USER_SETTINGS = 76
    """
    The device is unmanaged by user decision via settings plugin ('unmanaged-devices' for keyfile or
    'NM_CONTROLLED=no' for ifcfg-rh). Since: 1.48
    """

    NM_DEVICE_STATE_REASON_UNMANAGED_USER_UDEV = 77
    """
    The device is unmanaged via udev rule. Since: 1.48
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
    Same as NM_802_11_AP_SEC_KEY_MGMT_EAP_SUITE_B_192 addition for backwards compatibility
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

    NM_802_11_AP_FLAGS_P2P_IE = 0x00000010
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

    NM_DEVICE_TYPE_HSR = 33
    """
    A HSR/PRP device. Since: 1.46.
    """

    NM_DEVICE_TYPE_IPVLAN = 34
    """
    A IPVLAN device. Since: 1.52.
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


@unique
class NMRadioFlags(IntFlag):
    """
    Flags related to radio interfaces.

    Since: 1.38
    """

    NM_RADIO_FLAG_NONE = 0
    """
    An alias for numeric zero, no flags set.
    """

    NM_RADIO_FLAG_WLAN_AVAILABLE = 0x1
    """
    A Wireless LAN device or rfkill switch is detected in the system.
    """

    NM_RADIO_FLAG_WWAN_AVAILABLE = 0x2
    """
    A Wireless WAN device or rfkill switch is detected in the system.
    """


@unique
class NMState(IntEnum):
    """
    NMState values indicate the current overall networking state.
    """

    NM_STATE_UNKNOWN = 0
    """
    Networking state is unknown. This indicates a daemon error that makes it unable to reasonably
    assess the state. In such event the applications are expected to assume Internet connectivity
    might be present and not disable controls that require network access. The graphical shells may
    hide the network accessibility indicator altogether since no meaningful status indication can be
    provided.
    """

    NM_STATE_ASLEEP = 10
    """
    Networking is not enabled, the system is being suspended or resumed from suspend.
    """

    NM_STATE_DISCONNECTED = 20
    """
    There is no active network connection. The graphical shell should indicate no network
    connectivity and the applications should not attempt to access the network.
    """

    NM_STATE_DISCONNECTING = 30
    """
    Network connections are being cleaned up. The applications should tear down their network
    sessions.
    """

    NM_STATE_CONNECTING = 40
    """
    A network connection is being started. The graphical shell should indicate the network is being
    connected while the applications should still make no attempts to connect the network.
    """

    NM_STATE_CONNECTED_LOCAL = 50
    """
    There is only local IPv4 and/or IPv6 connectivity, but no default route to access the Internet.
    The graphical shell should indicate no network connectivity.
    """

    NM_STATE_CONNECTED_SITE = 60
    """
    There is only site-wide IPv4 and/or IPv6 connectivity. This means a default route is available,
    but the Internet connectivity check (see "Connectivity" property) did not succeed. The graphical
    shell should indicate limited network connectivity.
    """

    NM_STATE_CONNECTED_GLOBAL = 70
    """
    There is global IPv4 and/or IPv6 Internet connectivity. This means the Internet connectivity
    check succeeded, the graphical shell should indicate full network connectivity.
    """


@unique
class NMSettingWirelessCcx(IntFlag):
    """
    Cisco CCX (Cisco Compatible Extensions) flags for wireless settings
    """

    NM_SETTING_WIRELESS_CCX_DISABLE = 0x0
    """
    Disable CCX
    """

    NM_SETTING_WIRELESS_CCX_OPTIMIZED = 0x1
    """
    Enable support for all CCX features except AP-assisted roaming, AP-specified maximum transmit
    power, and radio management
    """

    NM_SETTING_WIRELESS_CCX_FULL = 0x2
    """
    Enable CCX
    """


class NMSettingWirelessSummitFlags(IntFlag):
    """
    NMSettingWirelessSummitFlags values indicate which summit settings should be used
    """

    NM_SETTING_WIRELESS_SUMMIT_FLAGS_NONE = 0x0
    """
    No flags
    """

    NM_SETTING_WIRELESS_SUMMIT_FLAGS_ROAM_MFP_DEAUTH = 0x1
    """
    Deauth before an mfp roam
    """

    NM_SETTING_WIRELESS_SUMMIT_FLAGS_ALL = 0x1
    """
    All flags enabled
    """


NM_SETTING_CONNECTION_DEFAULTS: Dict[str, Any] = {
    "auth-retries": -1,
    "autoconnect": True,
    "autoconnect-ports": -1,
    "autoconnect-priority": 0,
    "autoconnect-retries": -1,
    "autoconnect-slaves": (
        NMSettingConnectionAutoconnectSlaves.NM_SETTING_CONNECTION_AUTOCONNECT_SLAVES_DEFAULT
    ),
    "controller": None,
    "dns-over-tls": -1,
    "down-on-poweroff": -1,
    "gateway-ping-timeout": 0,
    "id": None,
    "interface-name": None,
    "ip-ping-addresses": [],
    "ip-ping-addresses-require-all": -1,
    "ip-ping-timeout": 0,
    "lldp": -1,
    "llmnr": -1,
    "master": None,         # Deprecated since version 1.46: Use 'controller' instead, this is just
                            # an alias.
    "mdns": -1,
    "metered": NMMetered.NM_METERED_UNKNOWN,
    "mptcp-flags": 0,
    "mud-url": None,
    "multi-connect": 0,
    "permissions": [],
    "port-type": None,
    "read-only": False,     # Deprecated since version 1.44: This property is deprecated and has no
                            # meaning.
    "secondaries": [],
    "slave-type": None,     # Deprecated since version 1.46: Use 'port-type' instead, this is just
                            # an alias.
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
https://networkmanager.dev/docs/api/latest/nm-settings-dbus.html
"""


NM_SETTING_IPCONFIG_DEFAULTS: Dict[str, Any] = {
    "address-data": None,
    "addresses": None,              # Deprecated
    "auto-route-ext-gw": NMTernary.NM_TERNARY_DEFAULT,
    "dad-timeout": -1,
    "dhcp-dscp": None,
    "dhcp-hostname": None,
    "dhcp-hostname-flags": 0,
    "dhcp-iaid": None,
    "dhcp-reject-servers": [],
    "dhcp-send-hostname": True,     # Deprecated since version 1.52: use the new version of
                                    # dhcp-send-hostname instead.
    "dhcp-send-hostname-v2": -1,
    "dhcp-send-release": NMTernary.NM_TERNARY_DEFAULT,
    "dhcp-timeout": 0,
    "dns": [],                      # Deprecated
    "dns-data": [],
    "dns-options": [],
    "dns-priority": 0,
    "dns-search": [],
    "gateway": None,
    "ignore-auto-dns": False,
    "ignore-auto-routes": False,
    "may-fail": True,
    "method": None,
    "never-default": False,
    "replace-local-rule": NMTernary.NM_TERNARY_DEFAULT,
    "required-timeout": -1,
    "route-data": None,
    "route-metric": -1,
    "route-table": 0,
    "routed-dns": -1,
    "routes": None,                 # Deprecated
    "routing-rules": None,
    "shared-dhcp-lease-time": 0,
    "shared-dhcp-range": None,
}
"""
Default values for the NM.SettingIPConfig settings. Values taken from:
https://lazka.github.io/pgi-docs/#NM-1.0/classes/SettingIPConfig.html
https://networkmanager.dev/docs/api/latest/nm-settings-dbus.html
"""


NM_SETTING_IP4CONFIG_DEFAULTS: Dict[str, Any] = {
    **NM_SETTING_IPCONFIG_DEFAULTS,
    "dhcp-client-id": None,
    "dhcp-fqdn": None,
    "dhcp-ipv6-only-preferred": -1,
    "dhcp-vendor-class-identifier": None,
    "link-local": 0,
}
"""
Default values for the NM.SettingIP4Config settings. Values taken from:
https://lazka.github.io/pgi-docs/#NM-1.0/classes/SettingIP4Config.html
https://networkmanager.dev/docs/api/latest/nm-settings-dbus.html
"""


NM_SETTING_IP6CONFIG_DEFAULTS: Dict[str, Any] = {
    **NM_SETTING_IPCONFIG_DEFAULTS,
    "addr-gen-mode": NMSettingIP6ConfigAddrGenMode.NM_SETTING_IP6_CONFIG_ADDR_GEN_MODE_DEFAULT,
    "dhcp-duid": None,
    "dhcp-pd-hint": None,
    "ip6-privacy": NMSettingIP6ConfigPrivacy.NM_SETTING_IP6_CONFIG_PRIVACY_UNKNOWN,
    "mtu": 0,
    "ra-timeout": 0,
    "temp-preferred-lifetime": 0,
    "temp-valid-lifetime": 0,
    "token": None,
}
"""
Default values for the NM.SettingIP6Config settings. Values taken from:
https://lazka.github.io/pgi-docs/#NM-1.0/classes/SettingIP6Config.html
https://networkmanager.dev/docs/api/latest/nm-settings-dbus.html
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
https://networkmanager.dev/docs/api/latest/nm-settings-dbus.html
"""


NM_SETTING_WIRED_DEFAULTS: Dict[str, Any] = {
    "accept-all-mac-addresses": NMTernary.NM_TERNARY_DEFAULT,
    "assigned-mac-address": None,
    "auto-negotiate": False,
    "cloned-mac-address": None,     # Deprecated
    "duplex": None,
    "generate-mac-address-mask": None,
    "mac-address": None,
    "mac-address-blacklist": [],
    "mac-address-denylist": [],
    "mtu": 0,
    "port": None,
    "s390-nettype": None,
    "s390-options": {},
    "s390-subchannels": [],
    "speed": 0,
    "wake-on-lan": 1,
    "wake-on-lan-password": None,
}
"""
Default values for the NM.SettingWired settings. Values taken from:
https://lazka.github.io/pgi-docs/#NM-1.0/classes/SettingWired.html
https://networkmanager.dev/docs/api/latest/nm-settings-dbus.html
"""


NM_SETTING_WIRELESS_DEFAULTS: Dict[str, Any] = {
    "acs": 0,                           # Summit feature
    "ap-config-file": None,             # Summit feature
    "ap-isolation": NMTernary.NM_TERNARY_DEFAULT,
    "assigned-mac-address": None,
    "auth-timeout": 0,                  # Summit feature
    "band": None,
    "bgscan": None,                     # Summit feature
    "bssid": None,
    "ccx": NMSettingWirelessCcx.NM_SETTING_WIRELESS_CCX_DISABLE,    # Summit feature
    "channel": 0,
    "channel-width": 0,
    "client-name": None,                # Summit feature
    "cloned-mac-address": None,         # Deprecated
    "dms": 0,                           # Summit feature
    "frequency-list": None,             # Summit feature
    "frequency-dfs": 1,                 # Summit feature
    "generate-mac-address-mask": None,
    "hidden": False,
    "mac-address": None,
    "mac-address-blacklist": [],
    "mac-address-denylist": [],
    "mac-address-randomization": 0,     # Deprecated since version 1.4: Use the NM.SettingWireless
                                        # :cloned-mac-address property instead.
    "max-scan-interval": 0,             # Summit feature
    "mode": None,
    "mtu": 0,
    "powersave": 0,
    "rate": 0,                          # Deprecated since version 1.44: This property is not
                                        # implemented and has no effect.
    "scan-delay": 0,                    # Summit feature
    "scan-dwell": 0,                    # Summit feature
    "scan-passive-dwell": 0,            # Summit feature
    "scan-suspend-time": 0,             # Summit feature
    "scan-roam-delta": 0,               # Summit feature
    "security": None,                   # Deprecated: This property is deprecated and has no
                                        # effect.
    "seen-bssids": [],
    "ssid": None,
    "summit-flags": NMSettingWirelessSummitFlags.NM_SETTING_WIRELESS_SUMMIT_FLAGS_NONE,  # Summit
                                                                                         # feature
    "tx-power": 0,                      # Deprecated since version 1.44: This property is not
                                        # implemented and has no effect.
    "wake-on-wlan": 1,
}
"""
Default values for the NM.SettingWireless settings. Values taken from:
https://lazka.github.io/pgi-docs/#NM-1.0/classes/SettingWireless.html
https://networkmanager.dev/docs/api/latest/nm-settings-dbus.html
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
    "wep-key-flags": NMSettingSecretFlags.NM_SETTING_SECRET_FLAG_NONE,
    "wep-key-type": NMWepKeyType.NM_WEP_KEY_TYPE_UNKNOWN,
    "wep-key0": None,
    "wep-key1": None,
    "wep-key2": None,
    "wep-key3": None,
    "wep-tx-keyidx": 0,
    "wps-method": 0,
}
"""
Default values for the NM.SettingWirelessSecurity settings. Values taken from:
https://lazka.github.io/pgi-docs/#NM-1.0/classes/SettingWirelessSecurity.html
https://networkmanager.dev/docs/api/latest/nm-settings-dbus.html
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
    "openssl-ciphers": None,
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
    "subject-match": None,  # Deprecated since version 1.2: Use "phase2-domain-suffix-match" instead
    "system-ca-certs": False,
}
"""
Default values for the NM.Setting8021x settings. Values taken from:
https://lazka.github.io/pgi-docs/#NM-1.0/classes/Setting8021x.html
https://networkmanager.dev/docs/api/latest/nm-settings-dbus.html
"""


NM_SETTING_GSM_DEFAULTS: Dict[str, Any] = {
    "apn": None,
    "auto-config": False,
    "device-id": None,
    "home-only": False,
    "initial-eps-bearer-apn": None,
    "initial-eps-bearer-configure": False,
    "initial-eps-bearer-noauth": True,
    "initial-eps-bearer-password": None,
    "initial-eps-bearer-password-flags": NMSettingSecretFlags.NM_SETTING_SECRET_FLAG_NONE,
    "initial-eps-bearer-refuse-chap": False,
    "initial-eps-bearer-refuse-eap": False,
    "initial-eps-bearer-refuse-mschap": False,
    "initial-eps-bearer-refuse-mschapv2": False,
    "initial-eps-bearer-refuse-pap": False,
    "initial-eps-bearer-username": None,
    "mtu": 0,
    "network-id": None,
    "number": None,     # Deprecated since version 1.16: User-provided values for this setting are
                        # no longer used.
    "password": None,
    "password-flags": NMSettingSecretFlags.NM_SETTING_SECRET_FLAG_NONE,
    "pin": None,
    "pin-flags": NMSettingSecretFlags.NM_SETTING_SECRET_FLAG_NONE,
    "sim-id": None,
    "sim-operator-id": None,
    "username": None,
}
"""
Default values for the NM.SettingGsm settings. Values taken from:
https://lazka.github.io/pgi-docs/#NM-1.0/classes/SettingGsm.html
https://networkmanager.dev/docs/api/latest/nm-settings-dbus.html
"""

SUMMIT_RCM_DEVTYPE_TEXT = {
    NMDeviceType.NM_DEVICE_TYPE_UNKNOWN: "Unknown",
    NMDeviceType.NM_DEVICE_TYPE_ETHERNET: "Ethernet",
    NMDeviceType.NM_DEVICE_TYPE_WIFI: "Wi-Fi",
    NMDeviceType.NM_DEVICE_TYPE_BT: "Bluetooth",
    NMDeviceType.NM_DEVICE_TYPE_OLPC_MESH: "OLPC",
    NMDeviceType.NM_DEVICE_TYPE_WIMAX: "WiMAX",
    NMDeviceType.NM_DEVICE_TYPE_MODEM: "Modem",
    NMDeviceType.NM_DEVICE_TYPE_INFINIBAND: "InfiniBand",
    NMDeviceType.NM_DEVICE_TYPE_BOND: "Bond",
    NMDeviceType.NM_DEVICE_TYPE_VLAN: "VLAN",
    NMDeviceType.NM_DEVICE_TYPE_ADSL: "ADSL",
    NMDeviceType.NM_DEVICE_TYPE_BRIDGE: "Bridge Master",
    NMDeviceType.NM_DEVICE_TYPE_GENERIC: "Generic",
    NMDeviceType.NM_DEVICE_TYPE_TEAM: "Team Master",
    NMDeviceType.NM_DEVICE_TYPE_TUN: "TUN/TAP",
    NMDeviceType.NM_DEVICE_TYPE_IP_TUNNEL: "IP Tunnel",
    NMDeviceType.NM_DEVICE_TYPE_MACVLAN: "MACVLAN",
    NMDeviceType.NM_DEVICE_TYPE_VXLAN: "VXLAN",
    NMDeviceType.NM_DEVICE_TYPE_VETH: "VETH",
    NMDeviceType.NM_DEVICE_TYPE_MACSEC: "MACsec",
    NMDeviceType.NM_DEVICE_TYPE_DUMMY: "dummy",
    NMDeviceType.NM_DEVICE_TYPE_PPP: "PPP",
    NMDeviceType.NM_DEVICE_TYPE_OVS_INTERFACE: "Open vSwitch interface",
    NMDeviceType.NM_DEVICE_TYPE_OVS_PORT: "Open vSwitch port",
    NMDeviceType.NM_DEVICE_TYPE_OVS_BRIDGE: "Open vSwitch bridge",
    NMDeviceType.NM_DEVICE_TYPE_WPAN: "WPAN",
    NMDeviceType.NM_DEVICE_TYPE_6LOWPAN: "6LoWPAN",
    NMDeviceType.NM_DEVICE_TYPE_WIREGUARD: "WireGuard",
    NMDeviceType.NM_DEVICE_TYPE_WIFI_P2P: "WiFi P2P",
    NMDeviceType.NM_DEVICE_TYPE_VRF: "VRF",
    NMDeviceType.NM_DEVICE_TYPE_LOOPBACK: "Loopback",
    NMDeviceType.NM_DEVICE_TYPE_HSR: "HSR/PRP",
    NMDeviceType.NM_DEVICE_TYPE_IPVLAN: "IPVLAN",
}
"""
Values from https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html
"""

SUMMIT_RCM_STATE_TEXT = {
    NMDeviceState.NM_DEVICE_STATE_UNKNOWN: "Unknown",
    NMDeviceState.NM_DEVICE_STATE_UNMANAGED: "Unmanaged",
    NMDeviceState.NM_DEVICE_STATE_UNAVAILABLE: "Unavailable",
    NMDeviceState.NM_DEVICE_STATE_DISCONNECTED: "Disconnected",
    NMDeviceState.NM_DEVICE_STATE_PREPARE: "Prepare",
    NMDeviceState.NM_DEVICE_STATE_CONFIG: "Config",
    NMDeviceState.NM_DEVICE_STATE_NEED_AUTH: "Need Auth",
    NMDeviceState.NM_DEVICE_STATE_IP_CONFIG: "IP Config",
    NMDeviceState.NM_DEVICE_STATE_IP_CHECK: "IP Check",
    NMDeviceState.NM_DEVICE_STATE_SECONDARIES: "Secondaries",
    NMDeviceState.NM_DEVICE_STATE_ACTIVATED: "Activated",
    NMDeviceState.NM_DEVICE_STATE_DEACTIVATING: "Deactivating",
    NMDeviceState.NM_DEVICE_STATE_FAILED: "Failed",
}
"""
Values from https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html
"""

SUMMIT_RCM_METERED_TEXT = {
    0: "Unknown",
    1: "Metered",
    2: "Not metered",
    3: "Metered (guessed)",
    4: "Not metered (guessed)",
}
"""
Values from https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html
"""

SUMMIT_RCM_CONNECTIVITY_STATE_TEXT = {
    0: "Unknown",
    1: "None",
    2: "Portal",
    3: "Limited",
    4: "Full",
}
"""
Values from https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html
"""

SUMMIT_RCM_802_11_MODE_STATE_TEXT = {
    NM80211Mode.NM_802_11_MODE_UNKNOWN: "Unknown",
    NM80211Mode.NM_802_11_MODE_ADHOC: "Ad-Hoc",
    NM80211Mode.NM_802_11_MODE_INFRA: "Infrastructure",
    NM80211Mode.NM_802_11_MODE_AP: "Access point",
    NM80211Mode.NM_802_11_MODE_MESH: "Mesh",
}
"""
Values from https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html
"""

SUMMIT_RCM_NM_ACTIVE_CONNECTION_STATE_TEXT = {
    NMActiveConnectionState.NM_ACTIVE_CONNECTION_STATE_UNKNOWN: "Unknown",
    NMActiveConnectionState.NM_ACTIVE_CONNECTION_STATE_ACTIVATING: "Activating",
    NMActiveConnectionState.NM_ACTIVE_CONNECTION_STATE_ACTIVATED: "Activated",
    NMActiveConnectionState.NM_ACTIVE_CONNECTION_STATE_DEACTIVATING: "Deactivating",
    NMActiveConnectionState.NM_ACTIVE_CONNECTION_STATE_DEACTIVATED: "Deactivated",
}
"""
Values from https://lazka.github.io/pgi-docs/#NM-1.0/enums.html
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


class NetworkManagerPropertyConverter:
    """
    Class to handle conversion between legacy and non-legacy property names for NetworkManager.
    """

    legacy: str = None
    non_legacy: str = None

    def __init__(self, legacy: str, non_legacy: str):
        self.legacy = legacy
        self.non_legacy = non_legacy


NM_PROPERTY_CONVERTER_NAMES: Dict[str, NetworkManagerPropertyConverter] = {
    "Ssid": NetworkManagerPropertyConverter(legacy="Ssid", non_legacy="ssid"),
    "HwAddress": NetworkManagerPropertyConverter(
        legacy="HwAddress", non_legacy="hwAddress"
    ),
    "MaxBitrate": NetworkManagerPropertyConverter(
        legacy="Maxbitrate", non_legacy="maxBitrate"
    ),
    "Flags": NetworkManagerPropertyConverter(legacy="Flags", non_legacy="flags"),
    "WpaFlags": NetworkManagerPropertyConverter(
        legacy="Wpaflags", non_legacy="wpaFlags"
    ),
    "RsnFlags": NetworkManagerPropertyConverter(
        legacy="Rsnflags", non_legacy="rsnFlags"
    ),
    "Bandwidth": NetworkManagerPropertyConverter(
        legacy="Bandwidth", non_legacy="bandwidth"
    ),
    "Strength": NetworkManagerPropertyConverter(
        legacy="Strength", non_legacy="strength"
    ),
    "Frequency": NetworkManagerPropertyConverter(
        legacy="Frequency", non_legacy="frequency"
    ),
    "Signal": NetworkManagerPropertyConverter(legacy="Signal", non_legacy="signal"),
    "Channel": NetworkManagerPropertyConverter(legacy="Channel", non_legacy="channel"),
    "State": NetworkManagerPropertyConverter(legacy="State", non_legacy="state"),
    "StateText": NetworkManagerPropertyConverter(
        legacy="StateText", non_legacy="stateText"
    ),
    "Mtu": NetworkManagerPropertyConverter(legacy="Mtu", non_legacy="mtu"),
    "DeviceType": NetworkManagerPropertyConverter(
        legacy="DeviceType", non_legacy="deviceType"
    ),
    "DeviceTypeText": NetworkManagerPropertyConverter(
        legacy="DeviceTypeText", non_legacy="deviceTypeText"
    ),
    "Addresses": NetworkManagerPropertyConverter(
        legacy="Addresses", non_legacy="addresses"
    ),
    "AddressData": NetworkManagerPropertyConverter(
        legacy="AddressData", non_legacy="addressData"
    ),
    "next-hop": NetworkManagerPropertyConverter(
        legacy="next_hop", non_legacy="nextHop"
    ),
    "Routes": NetworkManagerPropertyConverter(legacy="Routes", non_legacy="routes"),
    "RouteData": NetworkManagerPropertyConverter(
        legacy="RouteData", non_legacy="routeData"
    ),
    "Gateway": NetworkManagerPropertyConverter(legacy="Gateway", non_legacy="gateway"),
    "Domains": NetworkManagerPropertyConverter(legacy="Domains", non_legacy="domains"),
    "NameserverData": NetworkManagerPropertyConverter(
        legacy="NameserverData", non_legacy="nameservers"
    ),
    "WinsServerData": NetworkManagerPropertyConverter(
        legacy="WinsServerData", non_legacy="winsServers"
    ),
    "Options": NetworkManagerPropertyConverter(legacy="Options", non_legacy="options"),
    "PermHwAddress": NetworkManagerPropertyConverter(
        legacy="PermHwAddress", non_legacy="permHwAddress"
    ),
    "Speed": NetworkManagerPropertyConverter(legacy="Speed", non_legacy="speed"),
    "Carrier": NetworkManagerPropertyConverter(legacy="Carrier", non_legacy="carrier"),
    "Bitrate": NetworkManagerPropertyConverter(legacy="Bitrate", non_legacy="bitrate"),
    "Mode": NetworkManagerPropertyConverter(legacy="Mode", non_legacy="mode"),
    "RegDomain": NetworkManagerPropertyConverter(
        legacy="RegDomain", non_legacy="regDomain"
    ),
    "LastScan": NetworkManagerPropertyConverter(
        legacy="LastScan", non_legacy="lastScan"
    ),
    "interface-name": NetworkManagerPropertyConverter(
        legacy="interface-name", non_legacy="interfaceName"
    ),
    "connection_active": NetworkManagerPropertyConverter(
        legacy="connection_active", non_legacy="activeConnection"
    ),
    "Ip4Config": NetworkManagerPropertyConverter(
        legacy="ip4config", non_legacy="ip4Config"
    ),
    "Ip6Config": NetworkManagerPropertyConverter(
        legacy="ip6config", non_legacy="ip6Config"
    ),
    "Dhcp4Config": NetworkManagerPropertyConverter(
        legacy="dhcp4config", non_legacy="dhcp4Config"
    ),
    "Dhcp6Config": NetworkManagerPropertyConverter(
        legacy="dhcp6config", non_legacy="dhcp6Config"
    ),
    "ActiveAccessPoint": NetworkManagerPropertyConverter(
        legacy="activeaccesspoint", non_legacy="activeAccessPoint"
    ),
    "available_connections": NetworkManagerPropertyConverter(
        legacy="available_connections", non_legacy="availableConnections"
    ),
    "IpInterface": NetworkManagerPropertyConverter(
        legacy="ip_interface", non_legacy="ipInterface"
    ),
    "DriverVersion": NetworkManagerPropertyConverter(
        legacy="driver_version", non_legacy="driverVersion"
    ),
    "FirmwareVersion": NetworkManagerPropertyConverter(
        legacy="firmware_version", non_legacy="firmwareVersion"
    ),
    "StateReason": NetworkManagerPropertyConverter(
        legacy="state_reason", non_legacy="stateReason"
    ),
    "FirmwareMissing": NetworkManagerPropertyConverter(
        legacy="firmware_missing", non_legacy="firmwareMissing"
    ),
    "NmPluginMissing": NetworkManagerPropertyConverter(
        legacy="nm_plugin_missing", non_legacy="nmPluginMissing"
    ),
    "PhysicalPortId": NetworkManagerPropertyConverter(
        legacy="physical_port_id", non_legacy="physicalPortId"
    ),
    "MeteredText": NetworkManagerPropertyConverter(
        legacy="metered_text", non_legacy="meteredText"
    ),
    "LldpNeighbors": NetworkManagerPropertyConverter(
        legacy="lldp_neighbors", non_legacy="lldpNeighbors"
    ),
    "Ip4Connectivity": NetworkManagerPropertyConverter(
        legacy="ip4connectivity", non_legacy="ip4Connectivity"
    ),
    "Ip4ConnectivityText": NetworkManagerPropertyConverter(
        legacy="ip4connectivity_text", non_legacy="ip4ConnectivityText"
    ),
    "Ip6Connectivity": NetworkManagerPropertyConverter(
        legacy="ip6connectivity", non_legacy="ip6Connectivity"
    ),
    "Ip6ConnectivityText": NetworkManagerPropertyConverter(
        legacy="ip6connectivity_text", non_legacy="ip6ConnectivityText"
    ),
    "InterfaceFlags": NetworkManagerPropertyConverter(
        legacy="interface_flags", non_legacy="interfaceFlags"
    ),
}
"""
Dictionary used to convert property names from NetworkManager name to the legacy or non-legacy name.
This is used to ensure compatibility with both legacy and non-legacy property names.
For example, the property "MaxBitrate" can be accessed as "Maxbitrate" in legacy code or
"maxBitrate" in non-legacy code.
"""


def convert_nm_property_name(property_name: str, is_legacy: bool = False) -> str:
    """
    Convert a NetworkManager property name to either legacy or non-legacy format.

    :param name: The property name to convert.
    :param is_legacy: If True, convert to legacy format; if False, convert to non-legacy format.
    :return: The converted property name.
    """
    converter = NM_PROPERTY_CONVERTER_NAMES.get(property_name)
    if converter:
        return converter.legacy if is_legacy else converter.non_legacy

    # Return the original name camel-cased if no conversion is found
    return to_camel_case(property_name)


class NetworkManagerPropertiesWatcher:
    """
    Class to watch for changes in NetworkManager IP configuration. This class is used to monitor
    the state of NetworkManager IP configurations and trigger actions when the state changes.
    """

    def __init__(
        self, property_obj_path: str, device_interface_name: str, dev_lock: Lock
    ) -> None:
        self.property_obj_path = property_obj_path
        self.device_interface_name = device_interface_name
        self.bus = None
        self.proxy_object = None
        self.interface = None
        self.subscribed = False
        self.properties = {}
        self._dev_lock = dev_lock
        self.interface_name: str = ""

    async def subscribe(self) -> None:
        """
        Subscribe to NetworkManager property signals.
        """
        self.bus = await DBusManager().get_bus()
        self.proxy_object = self.bus.get_proxy_object(
            NetworkManagerService.NM_BUS_NAME,
            self.property_obj_path,
            await self.bus.introspect(
                NetworkManagerService.NM_BUS_NAME, self.property_obj_path
            ),
        )
        try:
            self.interface = self.proxy_object.get_interface(
                NetworkManagerService.DBUS_PROP_IFACE
            )
        except InterfaceNotFoundError:
            # This error can occur when the object at the given object path is "obsolete" (i.e.,
            # does not implement the standard DBus properties interface) by the time Summit RCM
            # attempts to access it. One example of this is the "ActiveAccessPoint" property of a
            # "Wireless" device which changes rapidly when bringing up an AP connection.
            self.subscribed = False
            return
        if self.interface_name:
            self.properties.update(
                await NetworkManagerService().get_obj_properties(
                    self.property_obj_path, self.interface_name
                )
            )
        self.interface.on_properties_changed(self.on_properties_changed)
        self.subscribed = True

    async def unsubscribe(self) -> None:
        """
        Unsubscribe from NetworkManager property signals.
        """
        if not self.subscribed:
            return

        if self.interface:
            self.interface.off_properties_changed(self.on_properties_changed)

        self.subscribed = False
        self.bus = None
        self.proxy_object = None
        self.interface = None

    async def on_properties_changed(
        self, _iface: str, changed_props: dict, _invalidated_props: list
    ) -> None:
        """
        Callback for property changes signal. This method is called when the
        properties of a NetworkManager configuration change.
        """

        async with self._dev_lock:
            self.properties.update(variant_to_python(changed_props))


class NetworkManagerIp4ConfigWatcher(NetworkManagerPropertiesWatcher):
    """
    Class to watch for changes in NetworkManager IPv4 configuration. This class is used to monitor
    the state of NetworkManager IPv4 configurations and trigger actions when the state changes.
    """

    def __init__(
        self, property_obj_path: str, device_interface_name: str, dev_lock: Lock
    ) -> None:
        super().__init__(property_obj_path, device_interface_name, dev_lock)
        self.interface_name = NetworkManagerService.NM_IP4CONFIG_IFACE


class NetworkManagerIp6ConfigWatcher(NetworkManagerPropertiesWatcher):
    """
    Class to watch for changes in NetworkManager IPv6 configuration. This class is used to monitor
    the state of NetworkManager IPv6 configurations and trigger actions when the state changes.
    """

    def __init__(
        self, property_obj_path: str, device_interface_name: str, dev_lock: Lock
    ) -> None:
        super().__init__(property_obj_path, device_interface_name, dev_lock)
        self.interface_name = NetworkManagerService.NM_IP6CONFIG_IFACE


class NetworkManagerDhcp4ConfigWatcher(NetworkManagerPropertiesWatcher):
    """
    Class to watch for changes in NetworkManager DHCP4 configuration. This class is used to monitor
    the state of NetworkManager DHCP4 configurations and trigger actions when the state changes.
    """

    def __init__(
        self, property_obj_path: str, device_interface_name: str, dev_lock: Lock
    ) -> None:
        super().__init__(property_obj_path, device_interface_name, dev_lock)
        self.interface_name = NetworkManagerService.NM_DHCP4CONFIG_IFACE


class NetworkManagerDhcp6ConfigWatcher(NetworkManagerPropertiesWatcher):
    """
    Class to watch for changes in NetworkManager DHCP6 configuration. This class is used to monitor
    the state of NetworkManager DHCP6 configurations and trigger actions when the state changes.
    """

    def __init__(
        self, property_obj_path: str, device_interface_name: str, dev_lock: Lock
    ) -> None:
        super().__init__(property_obj_path, device_interface_name, dev_lock)
        self.interface_name = NetworkManagerService.NM_DHCP6CONFIG_IFACE


class NetworkManagerActiveConnectionWatcher(NetworkManagerPropertiesWatcher):
    """
    Class to watch for changes in NetworkManager active connections. This class is used to monitor
    the state of NetworkManager active connections and trigger actions when the state changes.
    """

    def __init__(
        self, property_obj_path: str, device_interface_name: str, dev_lock: Lock
    ) -> None:
        super().__init__(property_obj_path, device_interface_name, dev_lock)
        self.interface_name = NetworkManagerService.NM_CONNECTION_ACTIVE_IFACE


class NetworkManagerActiveAccessPointWatcher(NetworkManagerPropertiesWatcher):
    """
    Class to watch for changes in NetworkManager active access points. This class is used to monitor
    the state of NetworkManager active access points and trigger actions when the state changes.
    """

    def __init__(
        self, property_obj_path: str, device_interface_name: str, dev_lock: Lock
    ) -> None:
        super().__init__(property_obj_path, device_interface_name, dev_lock)
        self.interface_name = NetworkManagerService.NM_ACCESS_POINT_IFACE


class NetworkManagerDeviceWatcher:
    """
    Class to watch for changes in NetworkManager devices. This class is used to monitor the state
    of NetworkManager devices and trigger actions when the state changes.
    """

    def __init__(
        self, device_obj_path: str, device_interface_name: str, device_properties: dict
    ) -> None:
        self.device_obj_path = device_obj_path
        self.device_interface_name = device_interface_name
        self.device_properties = device_properties
        self.bus = None
        self.proxy_object: Optional[ProxyObject] = None
        self.interface: Optional[ProxyInterface] = None
        self.subscribed = False
        self.dev_lock = Lock()
        self.ip4_config: Optional[NetworkManagerIp4ConfigWatcher] = None
        self.ip6_config: Optional[NetworkManagerIp6ConfigWatcher] = None
        self.dhcp4_config: Optional[NetworkManagerDhcp4ConfigWatcher] = None
        self.dhcp6_config: Optional[NetworkManagerDhcp6ConfigWatcher] = None
        self.active_connection: Optional[NetworkManagerActiveConnectionWatcher] = None
        self.active_access_point: Optional[NetworkManagerActiveAccessPointWatcher] = (
            None
        )

    async def subscribe(self) -> None:
        """
        Subscribe to NetworkManager device signals.
        """
        self.bus = await DBusManager().get_bus()
        self.proxy_object = self.bus.get_proxy_object(
            NetworkManagerService.NM_BUS_NAME,
            self.device_obj_path,
            await self.bus.introspect(
                NetworkManagerService.NM_BUS_NAME, self.device_obj_path
            ),
        )
        self.interface = self.proxy_object.get_interface(
            NetworkManagerService.DBUS_PROP_IFACE
        )
        self.interface.on_properties_changed(self.on_device_properties_changed)

        ip4_config_obj_path = self.device_properties.get("Ip4Config", "/")
        if ip4_config_obj_path != "/":
            self.ip4_config = NetworkManagerIp4ConfigWatcher(
                ip4_config_obj_path, self.device_interface_name, self.dev_lock
            )
            await self.ip4_config.subscribe()

        ip6_config_obj_path = self.device_properties.get("Ip6Config", "/")
        if ip6_config_obj_path != "/":
            self.ip6_config = NetworkManagerIp6ConfigWatcher(
                ip6_config_obj_path, self.device_interface_name, self.dev_lock
            )
            await self.ip6_config.subscribe()

        dhcp4_config_obj_path = self.device_properties.get("Dhcp4Config", "/")
        if dhcp4_config_obj_path != "/":
            self.dhcp4_config = NetworkManagerDhcp4ConfigWatcher(
                dhcp4_config_obj_path, self.device_interface_name, self.dev_lock
            )
            await self.dhcp4_config.subscribe()

        dhcp6_config_obj_path = self.device_properties.get("Dhcp6Config", "/")
        if dhcp6_config_obj_path != "/":
            self.dhcp6_config = NetworkManagerDhcp6ConfigWatcher(
                dhcp6_config_obj_path, self.device_interface_name, self.dev_lock
            )
            await self.dhcp6_config.subscribe()

        active_connection_obj_path = self.device_properties.get("ActiveConnection", "/")
        if active_connection_obj_path != "/":
            self.active_connection = NetworkManagerActiveConnectionWatcher(
                active_connection_obj_path, self.device_interface_name, self.dev_lock
            )
            await self.active_connection.subscribe()

        if (
            self.device_properties.get(
                "DeviceType", NMDeviceType.NM_DEVICE_TYPE_UNKNOWN
            )
            == NMDeviceType.NM_DEVICE_TYPE_WIFI
        ):
            active_access_point_obj_path = self.device_properties.get(
                "ActiveAccessPoint", "/"
            )
            if active_access_point_obj_path != "/":
                self.active_access_point = NetworkManagerActiveAccessPointWatcher(
                    active_access_point_obj_path,
                    self.device_interface_name,
                    self.dev_lock,
                )
                await self.active_access_point.subscribe()

        self.subscribed = True

    async def unsubscribe(self) -> None:
        """
        Unsubscribe from NetworkManager device signals.
        """
        if not self.subscribed:
            return

        if self.interface:
            self.interface.off_properties_changed(self.on_device_properties_changed)

        self.subscribed = False
        self.bus = None
        self.proxy_object = None
        self.interface = None

    async def on_device_properties_changed(
        self, _iface: str, changed_props: dict, _invalidated_props: list
    ) -> None:
        """
        Callback for device properties changed signal. This method is called when the properties
        of a NetworkManager device change.
        """

        async with self.dev_lock:
            changed_props = variant_to_python(changed_props)
            self.device_properties.update(changed_props)

            if "Ip4Config" in changed_props:
                if self.ip4_config is not None:
                    await self.ip4_config.unsubscribe()
                    self.ip4_config = None
                if changed_props.get("Ip4Config", "/") != "/":
                    # New Ip4Config object path is a valid object path, subscribe to it
                    self.ip4_config = NetworkManagerIp4ConfigWatcher(
                        changed_props["Ip4Config"],
                        self.device_interface_name,
                        self.dev_lock,
                    )
                    await self.ip4_config.subscribe()

            if "Ip6Config" in changed_props:
                if self.ip6_config is not None:
                    await self.ip6_config.unsubscribe()
                    self.ip6_config = None
                if changed_props.get("Ip6Config", "/") != "/":
                    # New Ip6Config object path is a valid object path, subscribe to it
                    self.ip6_config = NetworkManagerIp6ConfigWatcher(
                        changed_props["Ip6Config"],
                        self.device_interface_name,
                        self.dev_lock,
                    )
                    await self.ip6_config.subscribe()

            if "Dhcp4Config" in changed_props:
                if self.dhcp4_config is not None:
                    await self.dhcp4_config.unsubscribe()
                    self.dhcp4_config = None
                if changed_props.get("Dhcp4Config", "/") != "/":
                    # New Dhcp4Config object path is a valid object path, subscribe to it
                    self.dhcp4_config = NetworkManagerDhcp4ConfigWatcher(
                        changed_props["Dhcp4Config"],
                        self.device_interface_name,
                        self.dev_lock,
                    )
                    await self.dhcp4_config.subscribe()

            if "Dhcp6Config" in changed_props:
                if self.dhcp6_config is not None:
                    await self.dhcp6_config.unsubscribe()
                    self.dhcp6_config = None
                if changed_props.get("Dhcp6Config", "/") != "/":
                    # New Dhcp6Config object path is a valid object path, subscribe to it
                    self.dhcp6_config = NetworkManagerDhcp6ConfigWatcher(
                        changed_props["Dhcp6Config"],
                        self.device_interface_name,
                        self.dev_lock,
                    )
                    await self.dhcp6_config.subscribe()

            if "ActiveConnection" in changed_props:
                if self.active_connection is not None:
                    await self.active_connection.unsubscribe()
                    self.active_connection = None
                if changed_props.get("ActiveConnection", "/") != "/":
                    # New ActiveConnection object path is a valid object path, subscribe to it
                    self.active_connection = NetworkManagerActiveConnectionWatcher(
                        changed_props["ActiveConnection"],
                        self.device_interface_name,
                        self.dev_lock,
                    )
                    await self.active_connection.subscribe()

            if (
                self.device_properties.get(
                    "DeviceType", NMDeviceType.NM_DEVICE_TYPE_UNKNOWN
                )
                == NMDeviceType.NM_DEVICE_TYPE_WIFI
                and "ActiveAccessPoint" in changed_props
            ):
                if self.active_access_point is not None:
                    await self.active_access_point.unsubscribe()
                    self.active_access_point = None
                if changed_props.get("ActiveAccessPoint", "/") != "/":
                    # New ActiveAccessPoint object path is a valid object path, subscribe to it
                    self.active_access_point = NetworkManagerActiveAccessPointWatcher(
                        changed_props["ActiveAccessPoint"],
                        self.device_interface_name,
                        self.dev_lock,
                    )
                    await self.active_access_point.subscribe()


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

    subscribed: bool = False
    nm_devices: List[NetworkManagerDeviceWatcher] = []
    nm_systemd_service_state: str = "inactive"
    subscribed_to_nm_systemd_service_state: bool = False
    interface: Optional[ProxyInterface] = None
    lock: Lock = Lock()

    async def on_properties_changed(
        self, iface: str, changed_props: dict, _invalidated_props: list
    ) -> None:
        """
        Callback for NetworkManager properties changed signal. This method is called when the
        properties of NetworkManager itself change.
        """
        if not self.subscribed:
            # If not subscribed, ignore the signal. This can happen if the NetworkManager systemd
            # service itself is going up/down.
            syslog(
                "NetworkManagerService: Not subscribed, ignoring PropertiesChanged signal"
            )
            return

        # Handle changes to devices
        if iface == self.NM_CONNECTION_MANAGER_IFACE:
            changed_props = variant_to_python(changed_props)
            if "Devices" in changed_props:
                new_devices = changed_props["Devices"]
                current_device_paths = {dev.device_obj_path for dev in self.nm_devices}

                # Unsubscribe from devices that are no longer present
                for device in self.nm_devices:
                    if device.device_obj_path not in new_devices:
                        await device.unsubscribe()
                        self.nm_devices.remove(device)

                # Subscribe to new devices
                for dev_obj_path in new_devices:
                    if dev_obj_path not in current_device_paths:
                        dev_properties = await self.get_obj_properties(
                            dev_obj_path, self.NM_DEVICE_IFACE, timeout=10.0
                        )

                        # No need to check for "State" here, because "new" devices (e.g., a virtual
                        # interface to be used for AP+STA mode) may not have a valid/managed state
                        # at the time the PropertiesChanged signal is emitted.

                        interface_name = dev_properties.get("Interface", None)
                        if interface_name is None:
                            continue

                        if (
                            dev_properties.get(
                                "DeviceType", NMDeviceType.NM_DEVICE_TYPE_UNKNOWN
                            )
                            == NMDeviceType.NM_DEVICE_TYPE_WIFI
                        ):
                            # Read the wireless properties
                            dev_properties.update(
                                await self.get_obj_properties(
                                    dev_obj_path, self.NM_DEVICE_WIRELESS_IFACE
                                )
                            )

                        if (
                            dev_properties.get(
                                "DeviceType", NMDeviceType.NM_DEVICE_TYPE_UNKNOWN
                            )
                            == NMDeviceType.NM_DEVICE_TYPE_ETHERNET
                        ):
                            # Read the wired properties
                            dev_properties.update(
                                await self.get_obj_properties(
                                    dev_obj_path, self.NM_DEVICE_WIRED_IFACE
                                )
                            )

                        new_device = NetworkManagerDeviceWatcher(
                            device_obj_path=dev_obj_path,
                            device_interface_name=interface_name,
                            device_properties=dev_properties,
                        )
                        self.nm_devices.append(new_device)
                        await new_device.subscribe()

    async def nm_systemd_service_state_changed(self, new_state: str) -> None:
        """
        Callback for NetworkManager systemd service state changes. This method is called when the
        state of the NetworkManager systemd service changes.
        """
        # Use a lock to ensure thread safety when the state changes
        async with self.lock:
            current_state = self.nm_systemd_service_state
            self.nm_systemd_service_state = new_state

        if new_state == "active" and current_state == "activating":
            # Re-subscribe to NetworkManager signals
            await self.subscribe()
        elif new_state == "deactivating":
            # Unsubscribe from NetworkManager signals
            await self.unsubscribe()

    async def subscribe(self) -> None:
        """
        Subscribe to NetworkManager signals. This method should be called once to set up the
        subscription.
        """
        async with self.lock:
            syslog("NetworkManagerService: Subscribing to NetworkManager signals")
            if self.subscribed:
                syslog("NetworkManagerService: Already subscribed")
                return

            if not self.subscribed_to_nm_systemd_service_state:
                await NetworkManagerSystemdService().subscribe(
                    self.nm_systemd_service_state_changed
                )
                self.subscribed_to_nm_systemd_service_state = True

            bus = await DBusManager().get_bus()
            proxy_object = bus.get_proxy_object(
                self.NM_BUS_NAME,
                self.NM_CONNECTION_MANAGER_OBJ_PATH,
                await bus.introspect(
                    self.NM_BUS_NAME, self.NM_CONNECTION_MANAGER_OBJ_PATH
                ),
            )
            self.interface = proxy_object.get_interface(self.DBUS_PROP_IFACE)
            self.interface.on_properties_changed(self.on_properties_changed)
            self.subscribed = True

            for dev_obj_path in await self.get_all_devices():
                dev_properties = await self.get_obj_properties(
                    dev_obj_path,
                    self.NM_DEVICE_IFACE,
                    timeout=10.0,
                )
                dev_state = dev_properties.get(
                    "State", NMDeviceState.NM_DEVICE_STATE_UNKNOWN
                )
                if dev_state in [
                    NMDeviceState.NM_DEVICE_STATE_UNMANAGED,
                    NMDeviceState.NM_DEVICE_STATE_UNKNOWN,
                ]:
                    continue

                interface_name = dev_properties.get("Interface", None)
                if interface_name is None:
                    continue

                if (
                    dev_properties.get(
                        "DeviceType", NMDeviceType.NM_DEVICE_TYPE_UNKNOWN
                    )
                    == NMDeviceType.NM_DEVICE_TYPE_WIFI
                ):
                    # Read the wireless properties
                    dev_properties.update(
                        await self.get_obj_properties(
                            dev_obj_path, self.NM_DEVICE_WIRELESS_IFACE
                        )
                    )

                if (
                    dev_properties.get(
                        "DeviceType", NMDeviceType.NM_DEVICE_TYPE_UNKNOWN
                    )
                    == NMDeviceType.NM_DEVICE_TYPE_ETHERNET
                ):
                    # Read the wired properties
                    dev_properties.update(
                        await self.get_obj_properties(
                            dev_obj_path, self.NM_DEVICE_WIRED_IFACE
                        )
                    )

                new_device = NetworkManagerDeviceWatcher(
                    device_obj_path=dev_obj_path,
                    device_interface_name=interface_name,
                    device_properties=dev_properties,
                )
                self.nm_devices.append(new_device)
                await new_device.subscribe()
                syslog(
                    f"NetworkManagerService: Subscribed to device {interface_name} ({dev_obj_path})"
                )

            syslog("NetworkManagerService: Subscribed to NetworkManager signals")

    async def unsubscribe(self) -> None:
        """
        Unsubscribe from NetworkManager signals.
        """
        async with self.lock:
            syslog("NetworkManagerService: Unsubscribing from NetworkManager signals")
            if not self.subscribed:
                syslog("NetworkManagerService: Not subscribed, nothing to do")
                return

            if self.interface:
                self.interface.off_properties_changed(self.on_properties_changed)

            for device in self.nm_devices:
                try:
                    await device.unsubscribe()
                except Exception as e:
                    syslog(
                        f"Error unsubscribing from device {device.device_interface_name}: {e}"
                    )
            self.nm_devices = []
            self.subscribed = False
            self.interface = None
            syslog("NetworkManagerService: Unsubscribed from NetworkManager signals")

    @staticmethod
    def get_active_ap_rssi(ifname: Optional[str] = "wlan0") -> Tuple[bool, float]:
        """
        Retrieve the signal strength in dBm for the active accesspoint on the specified interface
        (default is wlan0).

        The return value is a tuple in the form of: (success, rssi)
        """
        iw = IW()
        try:
            for interface in iw.get_interfaces_dump():
                if str(interface.get_attr("NL80211_ATTR_IFNAME")) != ifname:
                    continue

                msg = nl80211cmd()
                msg["cmd"] = NL80211_NAMES["NL80211_CMD_GET_STATION"]
                msg["attrs"] = [
                    ["NL80211_ATTR_IFINDEX", interface.get_attr("NL80211_ATTR_IFINDEX")]
                ]

                res = iw.nlm_request(
                    msg, msg_type=iw.prid, msg_flags=NLM_F_REQUEST | NLM_F_DUMP
                )
                return (
                    True,
                    float(
                        res[0]
                        .get_attr("NL80211_ATTR_STA_INFO")
                        .get_attr("NL80211_STA_INFO_SIGNAL")
                    ),
                )

            # If not found, raise exception
            raise Exception("interface not found")
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to read RSSI value: {str(exception)}")
            return (False, INVALID_RSSI)
        finally:
            iw.close()

    @staticmethod
    def get_reg_domain_info() -> str:
        """
        Retrieve the radio's regulatory domain using 'netlink' (pyroute2)
        """
        iw = IW()
        try:
            res = iw.get_regulatory_domain()

            for phy in res:
                phy_name = phy.get_attr("NL80211_ATTR_WIPHY")
                if phy_name is None or phy_name != 0:
                    continue

                return str(phy.get_attr("NL80211_ATTR_REG_ALPHA2"))

            # If not found, raise exception
            raise Exception("interface not found")
        except Exception as exception:
            print(f"Unable to read reg domain: {str(exception)}")
            return "WW"
        finally:
            iw.close()

    @staticmethod
    def get_frequency_info(interface: str, frequency: int) -> int:
        """
        Retrieve the current frequency used by the given 'interface' as an int using 'frequency' as
        a default
        """
        iw = IW()
        try:
            for iface in iw.get_interfaces_dump():
                if str(iface.get_attr("NL80211_ATTR_IFNAME")) != interface:
                    continue

                return int(iface.get_attr("NL80211_ATTR_WIPHY_FREQ"))

            # If not found, raise exception
            raise Exception("interface not found")
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to read frequency value: {str(exception)}")
            return frequency
        finally:
            iw.close()

    @staticmethod
    def get_ap_properties(
        wireless_properties: dict,
        ap_props: Optional[dict],
        interface_name: str,
    ) -> dict:
        """
        Retrieve a dictionary of properties for an access point from the provided properities
        dictionaries and interface name
        """
        try:
            if not ap_props:
                return {}
            ap_properties = {}

            ssid = ap_props.get("Ssid", None)
            ap_properties["Ssid"] = ssid.decode("utf-8") if ssid is not None else ""
            ap_properties["HwAddress"] = ap_props.get("HwAddress", "")
            ap_properties["MaxBitrate"] = ap_props.get("MaxBitrate", 0)
            ap_properties["Flags"] = ap_props.get(
                "Flags", NM80211ApFlags.NM_802_11_AP_FLAGS_NONE
            )
            ap_properties["WpaFlags"] = ap_props.get(
                "WpaFlags", NM80211ApSecurityFlags.NM_802_11_AP_SEC_NONE
            )
            ap_properties["RsnFlags"] = ap_props.get(
                "RsnFlags", NM80211ApSecurityFlags.NM_802_11_AP_SEC_NONE
            )
            ap_properties["Bandwidth"] = ap_props.get("Bandwidth", 0)
            mode = int(
                wireless_properties.get("Mode", NM80211Mode.NM_802_11_MODE_UNKNOWN)
            )
            if mode == NM80211Mode.NM_802_11_MODE_AP:
                ap_properties["Strength"] = 100
                ap_properties["Frequency"] = NetworkManagerService().get_frequency_info(
                    interface_name, ap_props.get("Frequency", 0)
                )
                ap_properties["Signal"] = INVALID_RSSI
            else:
                ap_properties["Strength"] = ap_props.get("Strength", 0)
                ap_properties["Frequency"] = ap_props.get("Frequency", 0)
                (success, signal) = NetworkManagerService().get_active_ap_rssi(
                    interface_name
                )
                ap_properties["Signal"] = signal if success else INVALID_RSSI
            ap_properties["Channel"] = frequency_to_channel(ap_properties["Frequency"])
        except Exception as exception:
            syslog(f"Could not read AP properties: {str(exception)}")
            return {}

        return ap_properties

    @staticmethod
    async def get_dev_status(dev_properties: dict) -> dict:
        """
        Retrieve device status info from the provided dev_properties dictionary
        """
        status = {}
        status["State"] = int(
            dev_properties.get("State", NMDeviceState.NM_DEVICE_STATE_UNKNOWN)
        )
        try:
            status["StateText"] = SUMMIT_RCM_STATE_TEXT.get(status["State"])
        except Exception:
            status["StateText"] = "Unknown"
            syslog(
                f"unknown device state value {status['State']}."
                "See https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html"
            )
        status["Mtu"] = dev_properties.get("Mtu", 0)
        status["DeviceType"] = int(
            dev_properties.get("DeviceType", NMDeviceType.NM_DEVICE_TYPE_UNKNOWN)
        )
        try:
            status["DeviceTypeText"] = SUMMIT_RCM_DEVTYPE_TEXT.get(status["DeviceType"])
        except Exception:
            status["DeviceTypeText"] = "Unknown"
            syslog(
                f"unknown device type value {status['DeviceType']}."
                "See https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html"
            )
        return status

    @staticmethod
    async def get_ip4config_properties(props: dict, is_legacy: bool = False) -> dict:
        """
        Retrieve a dictionary of the IPv4 configuration properties (NM IP4Config) from the given
        dictionary
        """
        ipconfig_properties = {}

        try:
            addresses = {}
            address_data = []
            i = 0
            props_addresses = props.get("AddressData", None)
            if props_addresses is not None:
                for addr in props_addresses:
                    data = {}
                    data["address"] = (
                        variant_to_python(addr["address"])
                        if addr.get("address", None) is not None
                        else ""
                    )
                    data["prefix"] = (
                        variant_to_python(addr["prefix"])
                        if addr.get("prefix", None) is not None
                        else 0
                    )
                    address_data.append(data)
                    addresses[i] = data["address"] + "/" + str(data["prefix"])
                    i += 1
            if is_legacy:
                ipconfig_properties["Addresses"] = addresses
            ipconfig_properties["AddressData"] = address_data

            routes = {}
            route_data = []
            i = 0
            props_routes = props.get("RouteData", None)
            if props_routes is not None:
                for route in props_routes:
                    data = {}
                    data["dest"] = (
                        variant_to_python(route["dest"])
                        if route.get("dest", None) is not None
                        else ""
                    )
                    data["prefix"] = (
                        variant_to_python(route["prefix"])
                        if route.get("prefix", None) is not None
                        else 0
                    )
                    data["metric"] = (
                        variant_to_python(route["metric"])
                        if route.get("metric", None) is not None
                        else -1
                    )
                    data["next-hop"] = (
                        variant_to_python(route["next-hop"])
                        if route.get("next-hop", None) is not None
                        else ""
                    )
                    route_data.append(data)
                    routes[i] = (
                        data["dest"]
                        + "/"
                        + str(data["prefix"])
                        + " metric "
                        + str(data["metric"])
                    )
                    i += 1
            if is_legacy:
                ipconfig_properties["Routes"] = routes
            ipconfig_properties["RouteData"] = route_data
            ipconfig_properties["Gateway"] = props.get("Gateway", "")
            ipconfig_properties["Domains"] = []
            props_domains = (
                props["Domains"] if props.get("Domains", None) is not None else []
            )
            for domain in props_domains:
                ipconfig_properties["Domains"].append(domain)

            ipconfig_properties["NameserverData"] = []
            props_nameserver_data = (
                props["NameserverData"]
                if props.get("NameserverData", None) is not None
                else []
            )
            for nameserver in props_nameserver_data:
                ipconfig_properties["NameserverData"].append(
                    variant_to_python(nameserver["address"])
                )
            ipconfig_properties["WinsServerData"] = []
            props_wins_server_data = (
                props["WinsServerData"]
                if props.get("WinsServerData", None) is not None
                else []
            )
            for wins_server in props_wins_server_data:
                ipconfig_properties["WinsServerData"].append(wins_server)
        except Exception as exception:
            syslog(f"Could not retrieve IPv4 configuration - {str(exception)}")
            return {}

        return ipconfig_properties

    @staticmethod
    async def get_ip6config_properties(props: dict, is_legacy: bool = False) -> dict:
        """
        Retrieve a dictionary of the IPv6 configuration properties (NM IP6Config) from the given
        dictionary
        """
        ipconfig_properties = {}

        try:
            addresses = {}
            address_data = []
            i = 0
            props_addresses = props.get("AddressData", None)
            if props_addresses is not None:
                for addr in props_addresses:
                    data = {}
                    data["address"] = (
                        variant_to_python(addr["address"])
                        if addr.get("address", None) is not None
                        else ""
                    )
                    data["prefix"] = (
                        variant_to_python(addr["prefix"])
                        if addr.get("prefix", None) is not None
                        else 0
                    )
                    address_data.append(data)
                    addresses[i] = data["address"] + "/" + str(data["prefix"])
                    i += 1
            if is_legacy:
                ipconfig_properties["Addresses"] = addresses
            ipconfig_properties["AddressData"] = address_data

            routes = {}
            route_data = []
            i = 0
            props_routes = props.get("RouteData", None)
            if props_routes is not None:
                for route in props_routes:
                    data = {}
                    data["dest"] = (
                        variant_to_python(route["dest"])
                        if route.get("dest", None) is not None
                        else ""
                    )
                    data["prefix"] = (
                        variant_to_python(route["prefix"])
                        if route.get("prefix", None) is not None
                        else 0
                    )
                    data["metric"] = (
                        variant_to_python(route["metric"])
                        if route.get("metric", None) is not None
                        else -1
                    )
                    data["next-hop"] = (
                        variant_to_python(route["next-hop"])
                        if route.get("next-hop", None) is not None
                        else ""
                    )
                    route_data.append(data)
                    routes[i] = (
                        data["dest"]
                        + "/"
                        + str(data["prefix"])
                        + " metric "
                        + str(data["metric"])
                    )
                    i += 1
            if is_legacy:
                ipconfig_properties["Routes"] = routes
            ipconfig_properties["RouteData"] = route_data
            ipconfig_properties["Gateway"] = props.get("Gateway", "")
            ipconfig_properties["Domains"] = []
            props_domains = (
                props["Domains"] if props.get("Domains", None) is not None else []
            )
            for domain in props_domains:
                ipconfig_properties["Domains"].append(domain)
            ipconfig_properties["NameserverData"] = []
            props_nameservers = (
                props["Nameservers"]
                if props.get("Nameservers", None) is not None
                else []
            )
            for nameserver in props_nameservers:
                ipconfig_properties["NameserverData"].append(
                    inet_ntop(AF_INET6, nameserver)
                )
            if is_legacy:
                # Legacy WebLCM included a 'WinsServerData' entry, but this data is not exposed via
                # D-Bus by NetworkManager. So, only add this property for legacy requests.
                #
                # See below for more info:
                # https://people.freedesktop.org/~lkundrak/nm-docs/gdbus-org.freedesktop.NetworkManager.IP6Config.html
                ipconfig_properties["WinsServerData"] = []
        except Exception as exception:
            syslog(f"Could not retrieve IPv6 configuration - {str(exception)}")
            return {}

        return ipconfig_properties

    @staticmethod
    async def get_dhcp_config_properties(props: dict, is_legacy: bool = False) -> dict:
        """
        Retrieve a dictionary of the DHCP configuration properties (IPv4 or IPv6 baed on
        'interface') from the given dictionary
        """
        dhcpconfig_properties = {}

        try:
            options = props.get("Options", None)
            if options is not None:
                dhcpconfig_properties["Options"] = {}
                for option in options:
                    dhcpconfig_properties["Options"][
                        option if is_legacy else to_camel_case(option)
                    ] = variant_to_python(options[option])
        except Exception as ex:
            syslog(f"Error retrieving DHCP config properties: {str(ex)}")
            return {}

        return dhcpconfig_properties

    @staticmethod
    def get_wired_properties(wired_properties: dict) -> dict:
        """
        Retrieve a dictionary of properties for a wired (Ethernet) device with the provided
        dictionary
        """
        wired = {}
        wired["HwAddress"] = wired_properties.get("HwAddress", "")
        wired["PermHwAddress"] = wired_properties.get("PermHwAddress", "")
        wired["Speed"] = wired_properties.get("Speed", 0)
        wired["Carrier"] = wired_properties.get("Carrier", False)
        wired["S390Subchannels"] = wired_properties.get("S390Subchannels", [])
        return wired

    @staticmethod
    def get_wifi_properties(wireless_properties: dict) -> dict:
        """
        Retrieve a dictionary of properties for a wireless (Wi-Fi) device with the provided
        dictionary
        """
        wireless = {}
        wireless["Bitrate"] = wireless_properties.get("Bitrate", 0)
        wireless["HwAddress"] = wireless_properties.get("HwAddress", "")
        wireless["PermHwAddress"] = wireless_properties.get("PermHwAddress", "")
        wireless["Mode"] = int(
            wireless_properties.get("Mode", NM80211Mode.NM_802_11_MODE_UNKNOWN)
        )
        wireless["RegDomain"] = NetworkManagerService().get_reg_domain_info()
        wireless["LastScan"] = int(wireless_properties.get("LastScan", -1))
        return wireless

    @staticmethod
    async def get_active_connection(dev_props: dict) -> dict:
        """
        Retrieve the 'connection' settings for the 'ActiveConnection' of the provided device
        """
        # Retrieve the active connection object path from the provided device's properties
        active_connection_obj_path = dev_props.get("ActiveConnection", None)
        if not active_connection_obj_path:
            return {}

        # Retrieve the active connection's properties
        try:
            active_connection_props = await NetworkManagerService().get_obj_properties(
                active_connection_obj_path,
                NetworkManagerService().NM_CONNECTION_ACTIVE_IFACE,
            )
        except Exception:
            return {}

        # Retrive the active connection's 'Connection' object path
        active_connection_conn_obj_path = active_connection_props.get("Connection", "")
        if active_connection_conn_obj_path == "":
            return {}

        # Retrieve the active connection's 'Connection' properties
        active_connection_conn_props = (
            await NetworkManagerService().get_connection_settings(
                active_connection_conn_obj_path
            )
        )

        # Retrieve the 'connection' settings property
        setting_connection = active_connection_conn_props.get("connection", None)
        if setting_connection is None:
            return {}

        # Retrieve the Pythonic value for each parameter
        for param in setting_connection:
            setting_connection[param] = setting_connection[param].value

        return setting_connection

    @staticmethod
    async def get_available_connections(dev_props: dict) -> list:
        """
        Retrieve a list of 'Connection' settings for the available connections on the given device
        """
        # Retrieve the list of object paths for the available connections
        available_connections = dev_props.get("AvailableConnections", [])

        connections = []
        for connection_obj_path in available_connections:
            # Retrieve the connection's properties
            connection_conn_props = (
                await NetworkManagerService().get_connection_settings(
                    connection_obj_path
                )
            )

            # Retrieve the 'connection' settings property
            setting_connection = connection_conn_props.get("connection", None)
            if setting_connection is None:
                continue

            # Retrieve the Pythonic value for each parameter
            for param in setting_connection:
                setting_connection[param] = setting_connection[param].value

            connections.append(setting_connection)

        return connections

    def convert_property_names(self, status: dict, is_legacy: bool = False) -> dict:
        """
        Convert property names in the status dictionary to either legacy or non-legacy format.
        :param status: The status dictionary containing property names to convert.
        :param is_legacy: If True, convert to legacy format; if False, convert to non-legacy format.
        :return: A new dictionary with converted property names.
        """
        converted_dict = {}
        for key, value in status.items():
            if isinstance(value, dict):
                try:
                    converted_dict[convert_nm_property_name(key, is_legacy)] = (
                        self.convert_property_names(value, is_legacy)
                    )
                except Exception:
                    converted_dict[key] = value
            elif isinstance(value, list):
                converted_list = []
                for item in value:
                    if isinstance(item, dict):
                        converted_list.append(
                            self.convert_property_names(item, is_legacy)
                        )
                    else:
                        converted_list.append(item)
                try:
                    converted_dict[convert_nm_property_name(key, is_legacy)] = (
                        converted_list
                    )
                except Exception:
                    converted_dict[key] = converted_list
            else:
                try:
                    converted_dict[convert_nm_property_name(key, is_legacy)] = value
                except Exception:
                    converted_dict[key] = value

        return converted_dict

    async def get_status(
        self, is_legacy: bool = False, timeout: Optional[float] = None
    ) -> dict:
        """
        Get the cached status of NetworkManager. This method retrieves the current status of
        NetworkManager, including connectivity, devices, and active connections.
        :param is_legacy: If True, format response in legacy format.
        :param timeout: Optional timeout for the operation.
        :return: A dictionary containing the status of NetworkManager.
        """
        status = {}

        for device in self.nm_devices:
            async with device.dev_lock:
                dev_properties = device.device_properties
                dev_state = dev_properties.get(
                    "State", NMDeviceState.NM_DEVICE_STATE_UNKNOWN
                )
                status[device.device_interface_name] = {}

                status[device.device_interface_name]["status"] = (
                    await self.get_dev_status(dev_properties)
                )

                if dev_state == NMDeviceState.NM_DEVICE_STATE_ACTIVATED:
                    if device.active_connection is not None:
                        active_connection_connection_obj_path = (
                            device.active_connection.properties.get("Connection", None)
                        )
                        if active_connection_connection_obj_path is not None:
                            active_connection_connection_settings = (
                                await self.get_connection_settings(
                                    active_connection_connection_obj_path,
                                    timeout=timeout,
                                )
                            )

                            setting_connection = (
                                active_connection_connection_settings.get(
                                    "connection", None
                                )
                            )
                            if setting_connection is not None:
                                connection_active = {}
                                connection_active["id"] = (
                                    setting_connection["id"].value
                                    if setting_connection.get("id", None) is not None
                                    else ""
                                )
                                connection_active["interface-name"] = (
                                    setting_connection["interface-name"].value
                                    if setting_connection.get("interface-name", None)
                                    is not None
                                    else ""
                                )
                                connection_active["permissions"] = (
                                    setting_connection["permissions"].value
                                    if setting_connection.get("permissions", None)
                                    is not None
                                    else []
                                )
                                connection_active["type"] = (
                                    setting_connection["type"].value
                                    if setting_connection.get("type", None) is not None
                                    else ""
                                )
                                connection_active["uuid"] = (
                                    setting_connection["uuid"].value
                                    if setting_connection.get("uuid", None) is not None
                                    else ""
                                )
                                connection_active["zone"] = (
                                    setting_connection["zone"].value
                                    if setting_connection.get("zone", None) is not None
                                    else ""
                                )
                                status[device.device_interface_name][
                                    "connection_active"
                                ] = connection_active

                    status[device.device_interface_name]["Ip4Config"] = (
                        await self.get_ip4config_properties(
                            device.ip4_config.properties if device.ip4_config else {},
                            is_legacy=is_legacy,
                        )
                    )

                    status[device.device_interface_name]["Ip6Config"] = (
                        await self.get_ip6config_properties(
                            device.ip6_config.properties if device.ip6_config else {},
                            is_legacy=is_legacy,
                        )
                    )

                    status[device.device_interface_name]["Dhcp4Config"] = (
                        await self.get_dhcp_config_properties(
                            (
                                device.dhcp4_config.properties
                                if device.dhcp4_config
                                else {}
                            ),
                            is_legacy=is_legacy,
                        )
                    )

                    status[device.device_interface_name]["Dhcp6Config"] = (
                        await self.get_dhcp_config_properties(
                            (
                                device.dhcp6_config.properties
                                if device.dhcp6_config
                                else {}
                            ),
                            is_legacy=is_legacy,
                        )
                    )

                if (
                    status[device.device_interface_name]["status"].get(
                        "DeviceType", NMDeviceType.NM_DEVICE_TYPE_UNKNOWN
                    )
                    == NMDeviceType.NM_DEVICE_TYPE_ETHERNET
                ):
                    status[device.device_interface_name]["wired"] = (
                        self.get_wired_properties(device.device_properties)
                    )

                if (
                    status[device.device_interface_name]["status"].get(
                        "DeviceType", NMDeviceType.NM_DEVICE_TYPE_UNKNOWN
                    )
                    == NMDeviceType.NM_DEVICE_TYPE_WIFI
                ):
                    status[device.device_interface_name]["wireless"] = (
                        self.get_wifi_properties(
                            device.device_properties,
                        )
                    )
                    if dev_state == NMDeviceState.NM_DEVICE_STATE_ACTIVATED:
                        status[device.device_interface_name]["ActiveAccessPoint"] = (
                            self.get_ap_properties(
                                device.device_properties,
                                (
                                    device.active_access_point.properties
                                    if device.active_access_point
                                    else {}
                                ),
                                device.device_interface_name,
                            )
                        )

        return self.convert_property_names(status, is_legacy)

    async def get_interface_status(
        self, target_interface_name: str, is_legacy: bool = False
    ) -> dict:
        """
        Get the status of a specific interface by its name.
        :param target_interface_name: The name of the interface to retrieve status for.
        :param is_legacy: If True, format response in legacy format.
        :return: A dictionary containing the status of the specified interface.
        """
        dev_properties = {}

        if target_interface_name not in [
            device.device_interface_name for device in self.nm_devices
        ]:
            return {}

        status = await self.get_status(is_legacy=is_legacy)

        dev_properties = status.get(target_interface_name, {})

        for device in self.nm_devices:
            async with device.dev_lock:
                if device.device_interface_name != target_interface_name:
                    continue

                # If the device is found, retrieve its properties
                dev_props = device.device_properties

                # Read all NM device properties
                dev_properties["Udi"] = dev_props.get("Udi", "")
                dev_properties["path"] = device.device_obj_path
                dev_properties["interface"] = device.device_interface_name
                dev_properties["IpInterface"] = dev_props.get("IpInterface", "")
                dev_properties["Driver"] = dev_props.get("Driver", "")
                dev_properties["DriverVersion"] = dev_props.get("DriverVersion", "")
                dev_properties["FirmwareVersion"] = dev_props.get("FirmwareVersion", "")
                dev_properties["Capabilities"] = dev_props.get(
                    "Capabilities", NMDeviceCapabilities.NM_DEVICE_CAP_NONE
                )
                _, state_reason = dev_props.get(
                    "StateReason",
                    (
                        NMDeviceState.NM_DEVICE_STATE_UNKNOWN,
                        NMDeviceStateReason.NM_DEVICE_STATE_REASON_UNKNOWN,
                    ),
                )
                dev_properties["StateReason"] = state_reason
                dev_properties["connection_active"] = await self.get_active_connection(
                    dev_props
                )
                dev_properties["managed"] = bool(dev_props.get("Managed", False))
                dev_properties["Autoconnect"] = bool(
                    dev_props.get("Autoconnect", False)
                )
                dev_properties["FirmwareMissing"] = bool(
                    dev_props.get("FirmwareMissing", False)
                )
                dev_properties["NmPluginMissing"] = bool(
                    dev_props.get("NmPluginMissing", False)
                )
                dev_properties["available_connections"] = (
                    await self.get_available_connections(dev_props)
                )
                dev_properties["PhysicalPortId"] = dev_props.get("PhysicalPortId", "")
                dev_properties["Metered"] = int(dev_props.get("Metered", 0))
                dev_properties["MeteredText"] = SUMMIT_RCM_METERED_TEXT.get(
                    dev_properties["Metered"]
                )
                try:
                    lldp_neighbors = dev_props.get("LldpNeighbors", [])
                    lldp_neighbors = [neighbor.value for neighbor in lldp_neighbors]
                except Exception:
                    lldp_neighbors = []
                dev_properties["LldpNeighbors"] = lldp_neighbors
                dev_properties["Real"] = bool(dev_props.get("Real", False))
                dev_properties["Ip4Connectivity"] = int(
                    dev_props.get(
                        "Ip4Connectivity",
                        NMConnectivityState.NM_CONNECTIVITY_UNKNOWN,
                    )
                )
                dev_properties["Ip4ConnectivityText"] = (
                    SUMMIT_RCM_CONNECTIVITY_STATE_TEXT.get(
                        dev_properties["Ip4Connectivity"]
                    )
                )
                dev_properties["Ip6Connectivity"] = int(
                    dev_props.get(
                        "Ip6Connectivity",
                        NMConnectivityState.NM_CONNECTIVITY_UNKNOWN,
                    )
                )
                dev_properties["Ip6ConnectivityText"] = (
                    SUMMIT_RCM_CONNECTIVITY_STATE_TEXT.get(
                        dev_properties["Ip6Connectivity"]
                    )
                )
                dev_properties["InterfaceFlags"] = int(
                    dev_props.get(
                        "InterfaceFlags",
                        NMDeviceInterfaceFlags.NM_DEVICE_INTERFACE_FLAG_NONE,
                    )
                )

        return self.convert_property_names(dev_properties, is_legacy)

    async def get_all_devices(self, timeout: Optional[float] = None) -> List[str]:
        bus = await DBusManager().get_bus()

        reply = await wait_for(
            bus.call(
                Message(
                    destination=self.NM_BUS_NAME,
                    path=self.NM_CONNECTION_MANAGER_OBJ_PATH,
                    interface=self.NM_CONNECTION_MANAGER_IFACE,
                    member="GetAllDevices",
                )
            ),
            timeout=timeout,
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

    async def get_connection_settings(
        self, connection_obj_path: str, timeout: Optional[float] = None
    ) -> dict:
        bus = await DBusManager().get_bus()

        reply = await wait_for(
            bus.call(
                Message(
                    destination=self.NM_BUS_NAME,
                    path=connection_obj_path,
                    interface=self.NM_SETTINGS_CONNECTION_IFACE,
                    member="GetSettings",
                )
            ),
            timeout=timeout,
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

    async def get_obj_properties(
        self, obj_path: str, interface: str, timeout: Optional[float] = None
    ) -> dict:
        bus = await DBusManager().get_bus()

        reply = await wait_for(
            bus.call(
                Message(
                    destination=self.NM_BUS_NAME,
                    path=obj_path,
                    interface=self.DBUS_PROP_IFACE,
                    member="GetAll",
                    signature="s",
                    body=[interface],
                )
            ),
            timeout=timeout,
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
            str("file://{0}{1}\x00".format(FILEDIR_DICT.get("cert"), cert_name)),
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
                ] = f"{FILEDIR_DICT.get('pac')}{connection['802-1x']['pac-file']}"

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
