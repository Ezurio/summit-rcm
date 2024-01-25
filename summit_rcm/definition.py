import os
from enum import IntEnum
from summit_rcm.services.network_manager_service import (
    NM80211Mode,
    NMActiveConnectionState,
    NMDeviceState,
    NMDeviceType,
)

SUMMIT_RCM_VERSION = "11.0.0.216"

# TODO - deal with directories for file retrieval (see FIELDIR_DICT and files.py)
SYSTEM_CONF_DIR = "/data/"

NETWORKMANAGER_CONF_DIR = "/etc/NetworkManager/"
# summit-rcm.ini is for server config. It should be updated only by software update.
SUMMIT_RCM_SERVER_CONF_FILE = "/etc/summit-rcm.ini"
# system settings
SUMMIT_RCM_SETTINGS_FILE = "/etc/summit-rcm/summit-rcm-settings.ini"
# log forwarding
LOG_FORWARDING_ENABLED_FLAG_FILE = "/etc/summit-rcm/log_forwarding_enabled"

# timezone list
SUMMIT_RCM_ZONELIST_COMMAND = ["timedatectl", "list-timezones"]
SUMMIT_RCM_ZONEINFO = "/etc/localtime"
SUMMIT_RCM_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

WIFI_DRIVER_DEBUG_PARAM = "/sys/module/lrdmwl/parameters/lrd_debug"
# Change to ath6kl driver for wb50n
if not os.path.exists(WIFI_DRIVER_DEBUG_PARAM):
    WIFI_DRIVER_DEBUG_PARAM = "/sys/module/ath6kl_core/parameters/debug_mask"

FILEDIR_DICT = {
    "cert": "{0}{1}".format(NETWORKMANAGER_CONF_DIR, "certs/"),
    "pac": "{0}{1}".format(NETWORKMANAGER_CONF_DIR, "certs/"),
    "config": SYSTEM_CONF_DIR,
    "timezone": SUMMIT_RCM_ZONEINFO,
}

FILEFMT_DICT = {
    "cert": (".crt", ".key", ".pem", ".bin", ".der", ".p12", ".pfx", ".cer"),
    "pac": (".pac"),
}

DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"
WPA_OBJ = "/fi/w1/wpa_supplicant1"
WPA_IFACE = "fi.w1.wpa_supplicant1"

TIMEDATE1_BUS_NAME = "org.freedesktop.timedate1"
TIMEDATE1_MAIN_OBJ = "/org/freedesktop/timedate1"

LOGIND_BUS_NAME = "org.freedesktop.login1"
LOGIND_MAIN_OBJ = "/org/freedesktop/login1"
LOGIND_MAIN_IFACE = "org.freedesktop.login1.Manager"

SYSTEMD_BUS_NAME = "org.freedesktop.systemd1"
SYSTEMD_MAIN_OBJ = "/org/freedesktop/systemd1"
SYSTEMD_MANAGER_IFACE = "org.freedesktop.systemd1.Manager"
SYSTEMD_UNIT_IFACE = "org.freedesktop.systemd1.Unit"
SYSTEMD_UNIT_ACTIVE_STATE_PROP = "ActiveState"
SYSTEMD_UNIT_UNIT_FILE_STATE_PROP = "UnitFileState"
SYSTEMD_JOURNAL_GATEWAYD_SERVICE_FILE = "systemd-journal-gatewayd.service"
SYSTEMD_JOURNAL_GATEWAYD_SOCKET_FILE = "systemd-journal-gatewayd.socket"

SUMMIT_RCM_ERRORS = {
    "SDCERR_SUCCESS": 0,
    "SDCERR_FAIL": 1,
    "SDCERR_USER_LOGGED": 2,
    "SDCERR_USER_BLOCKED": 3,
    "SDCERR_SESSION_CHECK_FAILED": 4,
    "SDCERR_FIRMWARE_UPDATING": 5,
}

USER_PERMISSION_TYPES = {
    "UserPermissionTypes": [
        "status_networking",
        "networking_connections",
        "networking_edit",
        "networking_activate",
        "networking_ap_activate",
        "networking_delete",
        "networking_scan",
        "networking_certs",
        "logging",
        "help_version",
        "system_datetime",
        "system_swupdate",
        "system_password",
        "system_advanced",
        "system_positioning",
        "system_reboot",
        # Root only permissions
        "system_user",
    ],
    # Attributes to be displayed on the web
    "UserPermissionAttrs": [
        ["Networking Status", "checked", "disabled"],
        ["View Connections", "checked", "disabled"],
        ["Edit Connection", "", ""],
        ["Activate Connection", "", ""],
        ["Activate AP", "", ""],
        ["Delete Connection", "", ""],
        ["Wifi Scan", "", ""],
        ["Manage Certs", "", ""],
        ["Logging", "", ""],
        ["Version", "checked", "disabled"],
        ["Date & time", "", ""],
        ["Firmware Update", "", ""],
        ["Update Password", "checked", "disabled"],
        ["Advance Setting", "", ""],
        ["Positioning", "", ""],
        ["Reboot", "", ""],
        # Don't need to display root only permissions
        ["", "", ""],
    ],
}

# values from https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html
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
}

# values from https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html
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

# values from https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html
SUMMIT_RCM_METERED_TEXT = {
    0: "Unknown",
    1: "Metered",
    2: "Not metered",
    3: "Metered (guessed)",
    4: "Not metered (guessed)",
}

# values from https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html
SUMMIT_RCM_CONNECTIVITY_STATE_TEXT = {
    0: "Unknown",
    1: "None",
    2: "Portal",
    3: "Limited",
    4: "Full",
}

# values from https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html
SUMMIT_RCM_802_11_MODE_STATE_TEXT = {
    NM80211Mode.NM_802_11_MODE_UNKNOWN: "Unknown",
    NM80211Mode.NM_802_11_MODE_ADHOC: "Ad-Hoc",
    NM80211Mode.NM_802_11_MODE_INFRA: "Infrastructure",
    NM80211Mode.NM_802_11_MODE_AP: "Acces point",
    NM80211Mode.NM_802_11_MODE_MESH: "Mesh",
}

# values from https://lazka.github.io/pgi-docs/#NM-1.0/enums.html
SUMMIT_RCM_NM_ACTIVE_CONNECTION_STATE_TEXT = {
    NMActiveConnectionState.NM_ACTIVE_CONNECTION_STATE_UNKNOWN: "Unknown",
    NMActiveConnectionState.NM_ACTIVE_CONNECTION_STATE_ACTIVATING: "Activating",
    NMActiveConnectionState.NM_ACTIVE_CONNECTION_STATE_ACTIVATED: "Activated",
    NMActiveConnectionState.NM_ACTIVE_CONNECTION_STATE_DEACTIVATING: "Deactivating",
    NMActiveConnectionState.NM_ACTIVE_CONNECTION_STATE_DEACTIVATED: "Deactivated",
}


SUMMIT_RCM_NM_DEVICE_TYPE_WIRED_TEXT = "802-3-ethernet"
SUMMIT_RCM_NM_DEVICE_TYPE_WIRELESS_TEXT = "802-11-wireless"

SUMMIT_RCM_NM_SETTING_CONNECTION_TEXT = "connection"
SUMMIT_RCM_NM_SETTING_IP4_CONFIG_TEXT = "ipv4"
SUMMIT_RCM_NM_SETTING_IP6_CONFIG_TEXT = "ipv6"
SUMMIT_RCM_NM_SETTING_WIRED_TEXT = "802-3-ethernet"
SUMMIT_RCM_NM_SETTING_WIRELESS_TEXT = "802-11-wireless"
SUMMIT_RCM_NM_SETTING_WIRELESS_SECURITY_TEXT = "802-11-wireless-security"
SUMMIT_RCM_NM_SETTING_802_1X_TEXT = "802-1x"
SUMMIT_RCM_NM_SETTING_PROXY_TEXT = "proxy"
SUMMIT_RCM_NM_SETTING_GENERAL_TEXT = "GENERAL"
SUMMIT_RCM_NM_SETTING_IP4_TEXT = "IP4"
SUMMIT_RCM_NM_SETTING_IP6_TEXT = "IP6"
SUMMIT_RCM_NM_SETTING_DHCP4_TEXT = "DHCP4"
SUMMIT_RCM_NM_SETTING_DHCP6_TEXT = "DHCP6"
# file names for firmware-update and in-progress in sync with names in
# /usr/bin/modem_check_firmware_update.sh script
MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE = "/etc/modem/update-in-progress"
MODEM_FIRMWARE_UPDATE_FILE = "/etc/modem/firmware-update"
MODEM_FIRMWARE_UPDATE_DST_DIR = "/etc/modem"
MODEM_FIRMWARE_UPDATE_SRC_DIR = "/lib/firmware/modem"
# MODEM_ENABLE_FILE in sync with /usr/bin/modem_check_enable.sh
MODEM_ENABLE_FILE = "/etc/modem/modem_enabled"
MODEM_CONTROL_SERVICE_FILE = "modem-control.service"

INVALID_RSSI = -9999.9999

# Provisioning info
DEVICE_SERVER_KEY_PATH = "/etc/summit-rcm/provisioning/dev.key"
DEVICE_SERVER_CSR_PATH = "/etc/summit-rcm/provisioning/dev.csr"
DEVICE_SERVER_CERT_PATH = "/etc/summit-rcm/provisioning/dev.crt"
DEVICE_CA_CERT_CHAIN_PATH = "/etc/summit-rcm/ssl/ca.crt"
PROVISIONING_SERVER_KEY_PATH = "/etc/summit-rcm/ssl/provisioning.key"
PROVISIONING_SERVER_CERT_PATH = "/etc/summit-rcm/ssl/provisioning.crt"
PROVISIONING_CA_CERT_CHAIN_PATH = "/etc/summit-rcm/ssl/provisioning.ca.crt"
PROVISIONING_DIR = "/etc/summit-rcm/provisioning"
PROVISIONING_STATE_FILE_PATH = "/etc/summit-rcm/provisioning/state"
CERT_TEMP_PATH = "/tmp/dev.crt"
CONFIG_FILE_TEMP_PATH = "/tmp/dev.cnf"


class SSLModes(IntEnum):
    DISABLED = -1
    NO_AUTH = 0
    SERVER_VERIFY_CLIENT = 1
    CLIENT_VERIFY_SERVER = 2
    MUTUAL_AUTH = 3
