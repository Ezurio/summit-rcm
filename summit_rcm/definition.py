#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
import glob
import os
from enum import Enum, IntEnum

# TODO - deal with directories for file retrieval (see FIELDIR_DICT and files.py)
SYSTEM_CONF_DIR = "/etc"

NETWORKMANAGER_CONF_DIR = "/etc/NetworkManager/"
# summit-rcm.ini is for server config. It should be updated only by software update.
SUMMIT_RCM_SERVER_CONF_FILE = os.environ.get(
    "SUMMIT_RCM_SERVER_CONF_FILE", "/etc/summit-rcm.ini"
)
# system settings
SUMMIT_RCM_DATA_DIR = os.environ.get("SUMMIT_RCM_DATA_DIR", "/etc/summit-rcm")
SUMMIT_RCM_SETTINGS_FILE = os.environ.get(
    "SUMMIT_RCM_SETTINGS_FILE", "/etc/summit-rcm/summit-rcm-settings.ini"
)
# drop-in directory merged into the server config ini at parse time
SUMMIT_RCM_INI_DROPIN_DIR = os.getenv(
    "SUMMIT_RCM_INI_DROPIN_DIR", "/etc/summit-rcm.ini.d"
)


def resolve_ini_files(base_path: str) -> list[str]:
    """Return the base ini path (if it exists) followed by lexicographically sorted
    *.conf drop-ins from the drop-in directory. Later files override earlier ones
    when passed to ConfigParser.read()."""
    files = [base_path] if os.path.isfile(base_path) else []
    dropin_dir = SUMMIT_RCM_INI_DROPIN_DIR
    if os.path.isdir(dropin_dir):
        files += sorted(glob.glob(os.path.join(dropin_dir, "*.conf")))
    return files


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
PROVISIONING_DIR = "/etc/summit-rcm/provisioning"
PROVISIONING_SERVER_KEY_PATH = "/etc/summit-rcm/ssl/provisioning.key"
PROVISIONING_SERVER_CERT_PATH = "/etc/summit-rcm/ssl/provisioning.crt"
PROVISIONING_CA_CERT_CHAIN_PATH = "/etc/summit-rcm/ssl/provisioning.ca.crt"
CERT_TEMP_PATH = "/tmp/dev.crt"
CONFIG_FILE_TEMP_PATH = "/tmp/dev.cnf"


class SSLModes(IntEnum):
    """Enumeration of valid SSL modes for the server"""
    DISABLED = -1
    NO_AUTH = 0
    SERVER_VERIFY_CLIENT = 1
    CLIENT_VERIFY_SERVER = 2
    MUTUAL_AUTH = 3


class JournalctlLogTypesEnum(str, Enum):
    """Enumeration of valid journalctl log identifiers"""

    KERNEL = "kernel"
    NETWORK_MANAGER = "NetworkManager"
    SUMMIT_RCM = "summit-rcm"
    PYTHON = "python"
    ADAPTIVE_WW = "adaptive_ww"
    ALL = "All"


class SupplicantLogLevelEnum(str, Enum):
    """Enumeration of valid supplicant log levels"""

    NONE = "none"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"
    MSGDUMP = "msgdump"
    EXCESSIVE = "excessive"


class DriverLogLevelEnum(int, Enum):
    """Enumeration of valid Wi-Fi driver log levels"""

    DISABLED = 0
    ENABLED = 1


class PowerStateEnum(str, Enum):
    """Enumeration of valid power states"""

    ON = "on"
    OFF = "off"
    SUSPEND = "suspend"
    REBOOT = "reboot"


class RouteAdd():
    """Class to hold route add information"""

    def __init__(self, route):
        self.route = route
        self.awaited = False
