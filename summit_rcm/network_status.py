import os
from socket import inet_ntop, AF_INET, AF_INET6
from struct import pack
import time
from typing import Any, Optional, Tuple
import falcon
from threading import Lock
from .settings import ServerConfig, SystemSettingsManage
from . import definition
from syslog import syslog, LOG_ERR
from subprocess import run, TimeoutExpired
import re
from .network_manager_service import (
    NM_SETTING_8021X_DEFAULTS,
    NM_SETTING_CONNECTION_DEFAULTS,
    NM_SETTING_IP4CONFIG_DEFAULTS,
    NM_SETTING_IP6CONFIG_DEFAULTS,
    NM_SETTING_PROXY_DEFAULTS,
    NM_SETTING_WIRED_DEFAULTS,
    NM_SETTING_WIRELESS_DEFAULTS,
    NM_SETTING_WIRELESS_SECURITY_DEFAULTS,
    NM80211ApFlags,
    NM80211ApSecurityFlags,
    NM80211Mode,
    NMActiveConnectionState,
    NMDeviceState,
    NMDeviceType,
    NetworkManagerService,
)


class NetworkStatusHelper(object):

    _network_status = {}
    _lock = Lock()
    _IW_PATH = "/usr/sbin/iw"

    @classmethod
    def get_active_ap_rssi(cls, ifname: Optional[str] = "wlan0") -> Tuple[bool, float]:
        """
        Retrieve the signal strength in dBm for the active accesspoint on the specified interface
        (default is wlan0).

        The return value is a tuple in the form of: (success, rssi)
        """
        _RSSI_RE = r"signal: (?P<RSSI>.*) dBm"

        if not os.path.exists(cls._IW_PATH):
            return (False, definition.INVALID_RSSI)

        try:
            proc = run(
                [cls._IW_PATH, "dev", ifname, "link"],
                capture_output=True,
                timeout=SystemSettingsManage.get_user_callback_timeout(),
            )

            if not proc.returncode:
                for line in proc.stdout.decode("utf-8").splitlines():
                    line = line.strip()
                    match = re.match(_RSSI_RE, line)
                    if match:
                        return (True, float(match.group("RSSI")))
        except TimeoutExpired:
            syslog(LOG_ERR, f"Call 'iw dev {str(ifname)} link' timeout")
        except Exception as e:
            syslog(LOG_ERR, f"Call 'iw dev {str(ifname)} link' failed: {str(e)}")

        return (False, definition.INVALID_RSSI)

    @classmethod
    def get_reg_domain_info(cls):
        if not os.path.exists(cls._IW_PATH):
            return "WW"

        try:
            proc = run(
                [cls._IW_PATH, "reg", "get"],
                capture_output=True,
                timeout=SystemSettingsManage.get_user_callback_timeout(),
            )

            if not proc.returncode:
                s = re.split("phy#", proc.stdout.decode("utf-8"))
                # Return regulatory domain of phy#0
                m = re.search("country [A-Z][A-Z]", s[1] if len(s) > 1 else s[0])
                if m:
                    return m.group(0)[8:10]
        except TimeoutExpired:
            syslog(LOG_ERR, "Call 'iw reg get' timeout")
        except Exception as e:
            syslog(LOG_ERR, f"Call 'iw reg get' failed: {str(e)}")

        return "WW"

    @classmethod
    def get_frequency_info(cls, interface, frequency):
        if not os.path.exists(cls._IW_PATH):
            return frequency

        try:
            proc = run(
                [cls._IW_PATH, "dev"],
                capture_output=True,
                timeout=SystemSettingsManage.get_user_callback_timeout(),
            )
            if not proc.returncode:
                ifces = re.split("Interface", proc.stdout.decode("utf-8"))
                for ifce in ifces:
                    lines = ifce.splitlines()
                    if (lines[0].strip() != interface) or (len(lines) < 7):
                        continue
                    m = re.search("[2|5][0-9]{3}", lines[6])
                    if m:
                        return m.group(0)
        except TimeoutExpired:
            syslog(LOG_ERR, "Call 'iw dev' timeout")
        except Exception as e:
            syslog(LOG_ERR, f"Call 'iw dev' failed: {str(e)}")

        return frequency

    @classmethod
    def get_dev_status(cls, dev_properties: dict) -> dict:
        status = {}
        status["State"] = int(
            dev_properties.get("State", NMDeviceState.NM_DEVICE_STATE_UNKNOWN)
        )
        try:
            status["StateText"] = definition.SUMMIT_RCM_STATE_TEXT.get(status["State"])
        except Exception:
            status["StateText"] = "Unknown"
            syslog(
                "unknown device state value %d.  See https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html"
                % status["State"]
            )
        status["Mtu"] = dev_properties.get("Mtu", 0)
        status["DeviceType"] = int(
            dev_properties.get("DeviceType", NMDeviceState.NM_DEVICE_STATE_UNKNOWN)
        )
        try:
            status["DeviceTypeText"] = definition.SUMMIT_RCM_DEVTYPE_TEXT.get(
                status["DeviceType"]
            )
        except Exception:
            status["DeviceTypeText"] = "Unknown"
            syslog(
                "unknown device type value %d.  See https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html"
                % status["DeviceType"]
            )
        return status

    @classmethod
    async def get_ip4config_properties(cls, ipconfig_obj_path: str) -> dict:
        ipconfig_properties = {}
        if ipconfig_obj_path == "":
            return ipconfig_properties

        try:
            props = await NetworkManagerService().get_obj_properties(
                ipconfig_obj_path, NetworkManagerService().NM_IP4CONFIG_IFACE
            )

            addresses = {}
            address_data = []
            i = 0
            props_addresses = props.get("AddressData", None)
            if props_addresses is not None:
                for addr in props_addresses:
                    data = {}
                    data["address"] = (
                        addr["address"].value
                        if addr.get("address", None) is not None
                        else ""
                    )
                    data["prefix"] = (
                        addr["prefix"].value
                        if addr.get("prefix", None) is not None
                        else 0
                    )
                    address_data.append(data)
                    addresses[i] = data["address"] + "/" + str(data["prefix"])
                    i += 1
            ipconfig_properties["Addresses"] = addresses
            ipconfig_properties["AddressData"] = address_data

            routes = {}
            route_data = []
            i = 0
            props_routes = props.get("RouteData", None)
            if props_routes is not None:
                for rt in props_routes:
                    data = {}
                    data["dest"] = (
                        rt["dest"].value if rt.get("dest", None) is not None else ""
                    )
                    data["prefix"] = (
                        rt["prefix"].value if rt.get("prefix", None) is not None else 0
                    )
                    data["metric"] = (
                        rt["metric"].value if rt.get("metric", None) is not None else -1
                    )
                    data["next_hop"] = (
                        rt["next-hop"].value
                        if rt.get("next-hop", None) is not None
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
                nameserver["address"] = nameserver["address"].value
                ipconfig_properties["NameserverData"].append(nameserver)
            ipconfig_properties["WinsServerData"] = []
            props_wins_server_data = (
                props["WinsServerData"]
                if props.get("WinsServerData", None) is not None
                else []
            )
            for wins_server in props_wins_server_data:
                ipconfig_properties["WinsServerData"].append(wins_server)
        except Exception as e:
            syslog(f"Could not retrieve IPv4 configuration - {str(e)}")
            return {}

        return ipconfig_properties

    @classmethod
    async def get_ip6config_properties(cls, ipconfig_obj_path: str) -> dict:
        ipconfig_properties = {}
        if ipconfig_obj_path == "":
            return ipconfig_properties

        try:
            props = await NetworkManagerService().get_obj_properties(
                ipconfig_obj_path, NetworkManagerService().NM_IP6CONFIG_IFACE
            )

            addresses = {}
            address_data = []
            i = 0
            props_addresses = props.get("AddressData", None)
            if props_addresses is not None:
                for addr in props_addresses:
                    data = {}
                    data["address"] = (
                        addr["address"].value
                        if addr.get("address", None) is not None
                        else ""
                    )
                    data["prefix"] = (
                        addr["prefix"].value
                        if addr.get("prefix", None) is not None
                        else 0
                    )
                    address_data.append(data)
                    addresses[i] = data["address"] + "/" + str(data["prefix"])
                    i += 1
            ipconfig_properties["Addresses"] = addresses
            ipconfig_properties["AddressData"] = address_data

            routes = {}
            route_data = []
            i = 0
            props_routes = props.get("RouteData", None)
            if props_routes is not None:
                for rt in props_routes:
                    data = {}
                    data["dest"] = (
                        rt["dest"].value if rt.get("dest", None) is not None else ""
                    )
                    data["prefix"] = (
                        rt["prefix"].value if rt.get("prefix", None) is not None else 0
                    )
                    data["metric"] = (
                        rt["metric"].value if rt.get("metric", None) is not None else -1
                    )
                    data["next_hop"] = (
                        rt["next-hop"].value
                        if rt.get("next-hop", None) is not None
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
            ipconfig_properties["Routes"] = routes
            ipconfig_properties["RouteData"] = route_data
            ipconfig_properties["Gateway"] = props.get("Gateway", "")
            ipconfig_properties["Domains"] = []
            props_domains = (
                props["Domains"] if props.get("Domains", None) is not None else []
            )
            for domain in props_domains:
                ipconfig_properties["Domains"].append(domain)

            ipconfig_properties["Nameservers"] = []
            props_nameservers = (
                props["Nameservers"]
                if props.get("Nameservers", None) is not None
                else []
            )
            for nameserver in props_nameservers:
                ipconfig_properties["Nameservers"].append(
                    inet_ntop(AF_INET6, nameserver)
                )
        except Exception as e:
            syslog(f"Could not retrieve IPv6 configuration - {str(e)}")
            return {}

        return ipconfig_properties

    @classmethod
    async def get_dhcp_config_properties(
        cls, dhcpconfig_obj_path: str, interface: str
    ) -> dict:
        dhcpconfig_properties = {}
        if dhcpconfig_obj_path == "":
            return dhcpconfig_properties

        try:
            props = await NetworkManagerService().get_obj_properties(
                dhcpconfig_obj_path, interface
            )

            dhcpconfig_properties["Options"] = {}
            options = props.get("Options", None)
            if options is not None:
                for option in options:
                    dhcpconfig_properties["Options"][option] = options[option].value

        except Exception:
            return {}

        return dhcpconfig_properties

    @classmethod
    async def get_dhcp4_config_properties(cls, dhcpconfig_obj_path: str) -> dict:
        return await cls.get_dhcp_config_properties(
            dhcpconfig_obj_path, NetworkManagerService().NM_DHCP4CONFIG_IFACE
        )

    @classmethod
    async def get_dhcp6_config_properties(cls, dhcpconfig_obj_path: str) -> dict:
        return await cls.get_dhcp_config_properties(
            dhcpconfig_obj_path, NetworkManagerService().NM_DHCP6CONFIG_IFACE
        )

    @classmethod
    async def get_ap_properties(
        cls, wireless_properties: dict, interface_name: str
    ) -> dict:
        try:
            active_access_point_obj_path = wireless_properties.get(
                "ActiveAccessPoint", None
            )
            if (
                active_access_point_obj_path is None
                or active_access_point_obj_path == ""
            ):
                return {}
            ap_props = await NetworkManagerService().get_obj_properties(
                active_access_point_obj_path,
                NetworkManagerService().NM_ACCESS_POINT_IFACE,
            )
            ap_properties = {}

            ssid = ap_props.get("Ssid", None)
            ap_properties["Ssid"] = ssid.decode("utf-8") if ssid is not None else ""
            ap_properties["HwAddress"] = ap_props.get("HwAddress", "")
            ap_properties["Maxbitrate"] = ap_props.get("MaxBitrate", 0)
            ap_properties["Flags"] = ap_props.get(
                "Flags", NM80211ApFlags.NM_802_11_AP_FLAGS_NONE
            )
            ap_properties["Wpaflags"] = ap_props.get(
                "WpaFlags", NM80211ApSecurityFlags.NM_802_11_AP_SEC_NONE
            )
            ap_properties["Rsnflags"] = ap_props.get(
                "RsnFlags", NM80211ApSecurityFlags.NM_802_11_AP_SEC_NONE
            )
            # Use iw dev to get channel/frequency/rssi info for AP mode
            mode = ap_props.get("Mode", NM80211Mode.NM_802_11_MODE_UNKNOWN)
            if mode == NM80211Mode.NM_802_11_MODE_AP:
                ap_properties["Strength"] = 100
                ap_properties["Frequency"] = cls.get_frequency_info(
                    interface_name, ap_props.get("Frequency", 0)
                )
                ap_properties["Signal"] = definition.INVALID_RSSI
            else:
                ap_properties["Strength"] = ap_props.get("Strength", 0)
                ap_properties["Frequency"] = ap_props.get("Frequency", 0)
                (success, signal) = NetworkStatusHelper.get_active_ap_rssi(
                    interface_name
                )
                ap_properties["Signal"] = signal if success else definition.INVALID_RSSI
        except Exception as e:
            syslog(f"Could not read AP properties: {str(e)}")
            return {}

        return ap_properties

    @classmethod
    async def get_wifi_properties(cls, wireless_properties: dict) -> dict:
        wireless = {}
        wireless["Bitrate"] = wireless_properties.get("Bitrate", 0)
        wireless["PermHwAddress"] = wireless_properties.get("PermHwAddress", "")
        wireless["Mode"] = int(
            wireless_properties.get("Mode", NM80211Mode.NM_802_11_MODE_UNKNOWN)
        )
        wireless["RegDomain"] = NetworkStatusHelper.get_reg_domain_info()
        return wireless

    @classmethod
    async def get_wired_properties(cls, dev_obj_path: str) -> dict:
        wired = {}
        wired_properties = await NetworkManagerService().get_obj_properties(
            dev_obj_path, NetworkManagerService().NM_DEVICE_WIRED_IFACE
        )
        wired["PermHwAddress"] = wired_properties.get("PermHwAddress", "")
        wired["Speed"] = wired_properties.get("Speed", 0)
        wired["Carrier"] = wired_properties.get("Carrier", False)
        return wired

    @classmethod
    async def get_available_connections(cls, dev_props: dict) -> list:
        # Retrive the list of object paths for the available connections
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

    @classmethod
    async def get_active_connection(cls, dev_props: dict) -> dict:
        # Retrieve the active connection object path from the provided device's properties
        active_connection_obj_path = dev_props.get("ActiveConnection", None)
        if active_connection_obj_path is None:
            return {}

        # Retrieve the active connection's properties
        active_connection_props = await NetworkManagerService().get_obj_properties(
            active_connection_obj_path,
            NetworkManagerService().NM_CONNECTION_ACTIVE_IFACE,
        )

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

    @classmethod
    async def extract_general_properties_from_active_connection(
        cls, active_connection_props: dict
    ) -> dict:
        # Attempt to match output from:
        # 'nmcli connection show <target_profile>'
        properties = {}

        properties["name"] = active_connection_props.get("Id", None)
        properties["uuid"] = active_connection_props.get("Uuid", None)

        properties["devices"] = []
        for device_obj_path in active_connection_props.get("Devices", []):
            device_props = await NetworkManagerService().get_obj_properties(
                device_obj_path, NetworkManagerService().NM_DEVICE_IFACE
            )
            device = {}
            device["interface"] = device_props.get("Interface", None)
            device["ip-interface"] = device_props.get("IpInterface", None)
            properties["devices"].append(device)

        properties["state"] = definition.SUMMIT_RCM_NM_ACTIVE_CONNECTION_STATE_TEXT.get(
            active_connection_props.get(
                "State", NMActiveConnectionState.NM_ACTIVE_CONNECTION_STATE_UNKNOWN
            )
        )

        properties["default"] = active_connection_props.get("Default", False)
        properties["default6"] = active_connection_props.get("Default6", False)
        properties["specific-object-path"] = active_connection_props.get(
            "SpecificObject", None
        )
        properties["vpn"] = active_connection_props.get("Vpn", False)

        connection_obj_path = active_connection_props.get("Connection", "")
        properties["con-path"] = connection_obj_path
        connection_conn_props = await NetworkManagerService().get_connection_settings(
            connection_obj_path
        )
        connection_setting_connection = connection_conn_props.get("connection", None)
        properties["zone"] = (
            connection_setting_connection.get("zone", None)
            if connection_setting_connection is not None
            else None
        )

        properties["master-path"] = active_connection_props.get("Master", None)

        return properties

    @classmethod
    async def extract_ip4_config_properties_from_active_connection(
        cls, active_connection_props: dict
    ) -> dict:
        return await cls.extract_ip_config_properties_from_active_connection(
            active_connection_props=active_connection_props, is_ipv4=True
        )

    @classmethod
    async def extract_ip6_config_properties_from_active_connection(
        cls, active_connection_props: dict
    ) -> dict:
        return await cls.extract_ip_config_properties_from_active_connection(
            active_connection_props=active_connection_props, is_ipv4=False
        )

    @classmethod
    async def extract_ip_config_properties_from_active_connection(
        cls, active_connection_props: dict, is_ipv4: bool = True
    ) -> dict:
        ipconfig_obj_path = active_connection_props.get(
            "Ip4Config" if is_ipv4 else "Ip6Config", None
        )
        if ipconfig_obj_path is None:
            return None

        ipconfig_props = await NetworkManagerService().get_obj_properties(
            ipconfig_obj_path,
            NetworkManagerService().NM_IP4CONFIG_IFACE
            if is_ipv4
            else NetworkManagerService().NM_IP6CONFIG_IFACE,
        )

        # Attempt to match output from:
        # 'nmcli connection show <target_profile>'
        properties = {}

        properties["addresses"] = []
        properties["address-data"] = []
        for address in ipconfig_props.get("AddressData", []):
            try:
                properties["addresses"].append(
                    address["address"].value
                    if address.get("address", None) is not None
                    else ""
                    + "/"
                    + str(
                        address["prefix"].value
                        if address.get("prefix", None) is not None
                        else 0
                    )
                )
                properties["address-data"].append(
                    {
                        "address": address["address"].value
                        if address.get("address", None) is not None
                        else "",
                        "prefix": address["prefix"].value
                        if address.get("prefix", None) is not None
                        else 0,
                    }
                )
            except Exception:
                pass

        properties["domains"] = ipconfig_props.get("Domains", [])
        properties["gateway"] = ipconfig_props.get("Gateway", None)

        properties["dns"] = []
        nameservers = ipconfig_props.get("Nameservers", [])
        for nameserver in nameservers:
            properties["dns"].append(
                inet_ntop(
                    AF_INET if is_ipv4 else AF_INET6,
                    pack("L", nameserver) if is_ipv4 else nameserver,
                )
            )

        properties["routes"] = []
        properties["route-data"] = []
        for route in ipconfig_props.get("RouteData", []):
            try:
                properties["routes"].append(
                    route["dest"].value
                    if route.get("dest", None) is not None
                    else ""
                    + "/"
                    + str(
                        route["prefix"].value
                        if route.get("prefix", None) is not None
                        else 0
                    )
                    + " metirc "
                    + str(
                        route["metric"].value
                        if route.get("metric", None) is not None
                        else -1
                    )
                )
                properties["route-data"].append(
                    {
                        "dest": route["dest"].value
                        if route.get("dest", None) is not None
                        else "",
                        "prefix": route["prefix"].value
                        if route.get("prefix", None) is not None
                        else 0,
                        "next-hop": route["next-hop"].value
                        if route.get("next-hop", None) is not None
                        else None,
                        "metric": route["metric"].value
                        if route.get("metric", None) is not None
                        else -1,
                    }
                )
            except Exception:
                pass

        return properties

    @classmethod
    async def extract_dhcp4_config_properties_from_active_connection(
        cls, active_connection_props: dict
    ) -> dict:
        return await cls.extract_dhcp_config_properties_from_active_connection(
            active_connection_props=active_connection_props, is_ipv4=True
        )

    @classmethod
    async def extract_dhcp6_config_properties_from_active_connection(
        cls, active_connection_props: dict
    ) -> dict:
        return await cls.extract_dhcp_config_properties_from_active_connection(
            active_connection_props=active_connection_props, is_ipv4=False
        )

    @classmethod
    async def extract_dhcp_config_properties_from_active_connection(
        cls, active_connection_props: dict, is_ipv4: bool = True
    ) -> dict:
        dhcpconfig_obj_path = active_connection_props.get(
            "Dhcp4Config" if is_ipv4 else "Dhcp6Config", None
        )
        if dhcpconfig_obj_path is None:
            return None

        # Attempt to match output from:
        # 'nmcli connection show <target_profile>'
        properties = {}

        try:
            dhcpconfig_props = await NetworkManagerService().get_obj_properties(
                dhcpconfig_obj_path,
                NetworkManagerService().NM_DHCP4CONFIG_IFACE
                if is_ipv4
                else NetworkManagerService().NM_DHCP6CONFIG_IFACE,
            )

            properties["options"] = dhcpconfig_props.get("Options", [])

            if properties["options"] is not None:
                for option in properties["options"]:
                    properties["options"][option] = properties["options"][option].value
        except Exception:
            return None

        return properties

    @classmethod
    async def get_extended_connection_settings(cls, uuid: str) -> Tuple[int, str, dict]:
        if not uuid or uuid == "":
            return (-1, "Invalid UUID", {})

        settings = {}

        try:
            connection_obj_path = (
                await NetworkManagerService().get_connection_obj_path_by_uuid(str(uuid))
            )
        except Exception as e:
            return (-1, f"Invalid UUID - {str(e)}", {})

        if connection_obj_path == "":
            return (-1, "Invalid UUID", {})

        connection_conn_props = await NetworkManagerService().get_connection_settings(
            connection_obj_path
        )

        # 'connection' setting
        settings["connection"] = NM_SETTING_CONNECTION_DEFAULTS
        setting_connection = connection_conn_props.get("connection", None)
        if setting_connection is not None:
            for param in setting_connection:
                settings["connection"][param] = setting_connection[param].value

        # 'ipv4' setting
        settings["ipv4"] = NM_SETTING_IP4CONFIG_DEFAULTS
        setting_ipv4 = connection_conn_props.get("ipv4", None)
        if setting_ipv4 is not None:
            for param in setting_ipv4:
                # The 'addresses' and 'routes' properties are deprecated, use 'address-data' and
                # route-data' instead
                if param in ["addresses", "routes"]:
                    continue

                # The 'address-data' property require special processing
                if param == "address-data":
                    settings["ipv4"]["addresses"] = []
                    settings["ipv4"]["address-data"] = []
                    for item in setting_ipv4[param].value:
                        settings["ipv4"]["addresses"].append(
                            f"{item['address'].value}/{item['prefix'].value}"
                        )
                        settings["ipv4"]["address-data"].append(
                            {
                                "address": item["address"].value,
                                "prefix": item["prefix"].value,
                            }
                        )
                    continue

                # The 'route-data' property require special processing
                if param == "route-data":
                    settings["ipv4"]["routes"] = []
                    settings["ipv4"]["route-data"] = []
                    for item in setting_ipv4[param].value:
                        settings["ipv4"]["routes"].append(
                            item["address"].value
                            + "/"
                            + str(item["prefix"].value)
                            + " metric "
                            + str(item["metric"].value)
                        )
                        settings["ipv4"]["route-data"].append(
                            {
                                "dest": item["dest"].value,
                                "prefix": item["prefix"].value,
                                "next-hop": item["next-hop"].value,
                                "metric": item["metric"].value,
                            }
                        )
                    continue

                settings["ipv4"][param] = setting_ipv4[param].value

        # 'ipv6' setting
        settings["ipv6"] = NM_SETTING_IP6CONFIG_DEFAULTS
        setting_ipv6 = connection_conn_props.get("ipv6", None)
        if setting_ipv6 is not None:
            for param in setting_ipv6:
                # The 'addresses' and 'routes' properties are deprecated, use 'address-data' and
                # route-data' instead
                if param in ["addresses", "routes"]:
                    continue

                # The 'address-data' property require special processing
                if param == "address-data":
                    settings["ipv6"]["addresses"] = []
                    settings["ipv6"]["address-data"] = []
                    for item in setting_ipv6[param].value:
                        settings["ipv6"]["addresses"].append(
                            f"{item['address'].value}/{item['prefix'].value}"
                        )
                        settings["ipv6"]["address-data"].append(
                            {
                                "address": item["address"].value,
                                "prefix": item["prefix"].value,
                            }
                        )
                    continue

                # The 'route-data' property require special processing
                if param == "route-data":
                    settings["ipv6"]["routes"] = []
                    settings["ipv6"]["route-data"] = []
                    for item in setting_ipv6[param].value:
                        settings["ipv6"]["routes"].append(
                            item["address"].value
                            + "/"
                            + str(item["prefix"].value)
                            + " metric "
                            + str(item["metric"].value)
                        )
                        settings["ipv6"]["route-data"].append(
                            {
                                "dest": item["dest"].value,
                                "prefix": item["prefix"].value,
                                "next-hop": item["next-hop"].value,
                                "metric": item["metric"].value,
                            }
                        )
                    continue

                settings["ipv6"][param] = setting_ipv6[param].value

        # 'proxy' setting
        settings["proxy"] = NM_SETTING_PROXY_DEFAULTS
        setting_proxy = connection_conn_props.get("proxy", None)
        if setting_proxy is not None:
            for param in setting_proxy:
                settings["proxy"][param] = setting_proxy[param].value

        manager_props = await NetworkManagerService().get_obj_properties(
            NetworkManagerService().NM_CONNECTION_MANAGER_OBJ_PATH,
            NetworkManagerService().NM_CONNECTION_MANAGER_IFACE,
        )

        # Get settings only available if the requested connection is active
        active_connection_obj_paths = manager_props.get("ActiveConnections", [])
        for active_connection_obj_path in active_connection_obj_paths:
            active_connection_props = await NetworkManagerService().get_obj_properties(
                active_connection_obj_path,
                NetworkManagerService().NM_CONNECTION_ACTIVE_IFACE,
            )
            if active_connection_props.get("Uuid", "") == uuid:
                settings[
                    "GENERAL"
                ] = await cls.extract_general_properties_from_active_connection(
                    active_connection_props
                )
                settings["GENERAL"]["dbus-path"] = active_connection_obj_path
                settings[
                    "IP4"
                ] = await cls.extract_ip4_config_properties_from_active_connection(
                    active_connection_props
                )
                settings[
                    "IP6"
                ] = await cls.extract_ip6_config_properties_from_active_connection(
                    active_connection_props
                )
                settings[
                    "DHCP4"
                ] = await cls.extract_dhcp4_config_properties_from_active_connection(
                    active_connection_props
                )
                settings[
                    "DHCP6"
                ] = await cls.extract_dhcp6_config_properties_from_active_connection(
                    active_connection_props
                )
                break

        # Get type-specific connection settings (e.g., Wired, Wireless, etc.)
        if settings["connection"]["type"]:
            if (
                settings["connection"]["type"]
                == definition.SUMMIT_RCM_NM_DEVICE_TYPE_WIRED_TEXT
            ):
                settings[
                    definition.SUMMIT_RCM_NM_SETTING_WIRED_TEXT
                ] = NM_SETTING_WIRED_DEFAULTS
                setting_wired = connection_conn_props.get(
                    definition.SUMMIT_RCM_NM_SETTING_WIRED_TEXT, None
                )
                if setting_wired is not None:
                    for param in setting_wired:
                        settings[definition.SUMMIT_RCM_NM_SETTING_WIRED_TEXT][
                            param
                        ] = setting_wired[param].value

            if (
                settings["connection"]["type"]
                == definition.SUMMIT_RCM_NM_DEVICE_TYPE_WIRELESS_TEXT
            ):
                settings[
                    definition.SUMMIT_RCM_NM_SETTING_WIRELESS_TEXT
                ] = NM_SETTING_WIRELESS_DEFAULTS
                setting_wireless = connection_conn_props.get(
                    definition.SUMMIT_RCM_NM_SETTING_WIRELESS_TEXT, None
                )
                if setting_wireless is not None:
                    for param in setting_wireless:
                        # The 'ssid' property is returned as a bytearray and must be decoded
                        if param == "ssid":
                            settings[definition.SUMMIT_RCM_NM_SETTING_WIRELESS_TEXT][
                                param
                            ] = setting_wireless[param].value.decode("utf-8")
                            continue

                        settings[definition.SUMMIT_RCM_NM_SETTING_WIRELESS_TEXT][
                            param
                        ] = setting_wireless[param].value
                settings[definition.SUMMIT_RCM_NM_SETTING_WIRELESS_TEXT][
                    "RegDomain"
                ] = NetworkStatusHelper.get_reg_domain_info()

                settings[
                    definition.SUMMIT_RCM_NM_SETTING_WIRELESS_SECURITY_TEXT
                ] = NM_SETTING_WIRELESS_SECURITY_DEFAULTS
                setting_wireless_security = connection_conn_props.get(
                    definition.SUMMIT_RCM_NM_SETTING_WIRELESS_SECURITY_TEXT, None
                )
                if setting_wireless_security is not None:
                    for param in setting_wireless_security:
                        # Hide secret values
                        if param in [
                            "wep-key0",
                            "wep-key1",
                            "wep-key2",
                            "wep-key3",
                            "psk",
                            "leap-password",
                        ]:
                            settings[
                                definition.SUMMIT_RCM_NM_SETTING_WIRELESS_SECURITY_TEXT
                            ][param] = "<hidden>"
                            continue

                        settings[
                            definition.SUMMIT_RCM_NM_SETTING_WIRELESS_SECURITY_TEXT
                        ][param] = setting_wireless_security[param].value

            # Get 802.1x settings, if present
            setting_8021x = connection_conn_props.get(
                definition.SUMMIT_RCM_NM_SETTING_802_1X_TEXT, None
            )
            if setting_8021x is not None:
                settings[
                    definition.SUMMIT_RCM_NM_SETTING_802_1X_TEXT
                ] = NM_SETTING_8021X_DEFAULTS
                for param in setting_8021x:
                    # The following properties are omitted as they are binary blobs
                    if param in [
                        "ca-cert",
                        "client-cert",
                        "phase2-ca-cert",
                        "phase2-client-cert",
                        "phase2-private-key",
                        "private-key",
                    ]:
                        continue

                    # The following properties are passwords/secrets and are therefore hidden
                    if param in [
                        "ca-cert-password",
                        "client-cert-password",
                        "password",
                        "password-raw",
                        "phase2-ca-cert-password",
                        "phase2-client-cert-password",
                        "phase2-private-key-password",
                        "pin",
                        "private-key-password",
                    ]:
                        settings[definition.SUMMIT_RCM_NM_SETTING_802_1X_TEXT][
                            param
                        ] = "<hidden>"
                        continue

                    settings[definition.SUMMIT_RCM_NM_SETTING_802_1X_TEXT][
                        param
                    ] = setting_8021x[param].value

        return (0, "", settings)

    @classmethod
    async def network_status_query(cls):
        cls._network_status = {}
        dev_obj_paths = await NetworkManagerService().get_all_devices()
        for dev_obj_path in dev_obj_paths:
            dev_properties = await NetworkManagerService().get_obj_properties(
                dev_obj_path, NetworkManagerService().NM_DEVICE_IFACE
            )
            dev_state = dev_properties.get("State", None)
            if (
                dev_state is None
                or dev_state == NMDeviceState.NM_DEVICE_STATE_UNMANAGED
            ):
                continue

            interface_name = dev_properties.get("Interface", None)
            if interface_name is None:
                continue
            cls._network_status[interface_name] = {}

            cls._network_status[interface_name]["status"] = cls.get_dev_status(
                dev_properties
            )

            if dev_state == NMDeviceState.NM_DEVICE_STATE_ACTIVATED:
                dev_active_conn_obj_path = dev_properties.get("ActiveConnection", None)
                if dev_active_conn_obj_path is not None:
                    active_connection_properties = (
                        await NetworkManagerService().get_obj_properties(
                            dev_active_conn_obj_path,
                            NetworkManagerService().NM_CONNECTION_ACTIVE_IFACE,
                        )
                    )
                    active_connection_connection_obj_path = (
                        active_connection_properties.get("Connection", None)
                    )
                    if active_connection_connection_obj_path is not None:
                        active_connection_connection_settings = (
                            await NetworkManagerService().get_connection_settings(
                                active_connection_connection_obj_path
                            )
                        )

                        setting_connection = active_connection_connection_settings.get(
                            "connection", None
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
                            cls._network_status[interface_name][
                                "connection_active"
                            ] = connection_active

                cls._network_status[interface_name][
                    "ip4config"
                ] = await cls.get_ip4config_properties(
                    dev_properties.get("Ip4Config", "")
                )
                cls._network_status[interface_name][
                    "ip6config"
                ] = await cls.get_ip6config_properties(
                    dev_properties.get("Ip6Config", "")
                )
                cls._network_status[interface_name][
                    "dhcp4config"
                ] = await cls.get_dhcp4_config_properties(
                    dev_properties.get("Dhcp4Config", "")
                )
                cls._network_status[interface_name][
                    "dhcp6config"
                ] = await cls.get_dhcp6_config_properties(
                    dev_properties.get("Dhcp6Config", "")
                )

            if (
                cls._network_status[interface_name]["status"].get(
                    "DeviceType", NMDeviceType.NM_DEVICE_TYPE_UNKNOWN
                )
                == NMDeviceType.NM_DEVICE_TYPE_ETHERNET
            ):
                cls._network_status[interface_name][
                    "wired"
                ] = await cls.get_wired_properties(dev_obj_path)
                cls._network_status[interface_name]["wired"][
                    "HwAddress"
                ] = dev_properties.get("HwAddress", "")

            if (
                cls._network_status[interface_name]["status"].get(
                    "DeviceType", NMDeviceType.NM_DEVICE_TYPE_UNKNOWN
                )
                == NMDeviceType.NM_DEVICE_TYPE_WIFI
            ):
                wireless_properties = await NetworkManagerService().get_obj_properties(
                    dev_obj_path, NetworkManagerService().NM_DEVICE_WIRELESS_IFACE
                )
                cls._network_status[interface_name][
                    "wireless"
                ] = await cls.get_wifi_properties(wireless_properties)
                cls._network_status[interface_name]["wireless"][
                    "HwAddress"
                ] = dev_properties.get("HwAddress", "")
                if dev_state == NMDeviceState.NM_DEVICE_STATE_ACTIVATED:
                    cls._network_status[interface_name][
                        "activeaccesspoint"
                    ] = await cls.get_ap_properties(wireless_properties, interface_name)

    @classmethod
    def get_lock(cls):
        return cls._lock


async def dev_added(dev_obj_path: str) -> None:
    try:
        dev_properties = await NetworkManagerService().get_obj_properties(
            dev_obj_path, NetworkManagerService().NM_DEVICE_IFACE
        )
        interface_name = dev_properties.get("Interface", "")
        if interface_name == "":
            return
        NetworkStatusHelper._network_status[interface_name] = {}
        NetworkStatusHelper._network_status[interface_name][
            "status"
        ] = NetworkStatusHelper.get_dev_status(dev_properties)
    except Exception:
        pass


async def dev_removed(dev_obj_path):
    try:
        dev_properties = await NetworkManagerService().get_obj_properties(
            dev_obj_path, NetworkManagerService().NM_DEVICE_IFACE
        )
        interface_name = dev_properties.get("Interface", "")
        if interface_name == "":
            return
        NetworkStatusHelper._network_status.pop(interface_name, None)
    except Exception:
        pass


# def ap_propchange(ap, interface, signal, properties):
#     if "Strength" in properties:
#         for k in NetworkStatusHelper._network_status:
#             if NetworkStatusHelper._network_status[k].get("activeaccesspoint", None):
#                 if (
#                     NetworkStatusHelper._network_status[k]["activeaccesspoint"].get(
#                         "Ssid"
#                     )
#                     == ap.Ssid
#                 ):
#                     with NetworkStatusHelper._lock:
#                         NetworkStatusHelper._network_status[k]["activeaccesspoint"][
#                             "Strength"
#                         ] = properties["Strength"]


def dev_statechange(dev, new_state, old_state, reason):
    interface_name = dev.get_iface()
    if not interface_name:
        return
    if interface_name not in NetworkStatusHelper._network_status:
        NetworkStatusHelper._network_status[interface_name] = {}

    with NetworkStatusHelper._lock:
        if new_state == int(NM.DeviceState.ACTIVATED):
            NetworkStatusHelper._network_status[interface_name][
                "status"
            ] = NetworkStatusHelper.get_dev_status(dev)

            dev_active_connection = dev.get_active_connection()
            if dev_active_connection:
                active_connection = dev_active_connection.get_connection()
                setting_connection = active_connection.get_setting_connection()

                if setting_connection:
                    connection_active = {}
                    connection_active["id"] = setting_connection.get_id()
                    connection_active[
                        "interface-name"
                    ] = setting_connection.get_interface_name()
                    connection_active["permissions"] = setting_connection.get_property(
                        "permissions"
                    )
                    connection_active["type"] = setting_connection.get_property("type")
                    connection_active["uuid"] = setting_connection.get_uuid()
                    connection_active["zone"] = setting_connection.get_zone()
                    NetworkStatusHelper._network_status[interface_name][
                        "connection_active"
                    ] = connection_active

            NetworkStatusHelper._network_status[interface_name][
                "ip4config"
            ] = NetworkStatusHelper.get_ip4config_properties(dev.get_ip4_config())
            # NetworkStatusHelper._network_status[interface_name][
            #     "ip6config"
            # ] = NetworkStatusHelper.get_ipconfig_properties(dev.get_ip6_config())
            NetworkStatusHelper._network_status[interface_name][
                "dhcp4config"
            ] = NetworkStatusHelper.get_dhcp_config_properties(dev.get_dhcp4_config())
            NetworkStatusHelper._network_status[interface_name][
                "dhcp6config"
            ] = NetworkStatusHelper.get_dhcp_config_properties(dev.get_dhcp6_config())
        # 				dev.ActiveAccessPoint.OnPropertiesChanged(ap_propchange)
        elif new_state == int(NM.DeviceState.DISCONNECTED):
            if "ip4config" in NetworkStatusHelper._network_status[interface_name]:
                NetworkStatusHelper._network_status[interface_name].pop(
                    "ip4config", None
                )
            if "ip6config" in NetworkStatusHelper._network_status[interface_name]:
                NetworkStatusHelper._network_status[interface_name].pop(
                    "ip6config", None
                )
            if "dhcp4config" in NetworkStatusHelper._network_status[interface_name]:
                NetworkStatusHelper._network_status[interface_name].pop(
                    "dhcp4config", None
                )
            if "dhcp6config" in NetworkStatusHelper._network_status[interface_name]:
                NetworkStatusHelper._network_status[interface_name].pop(
                    "dhcp6config", None
                )
            if (
                "activeaccesspoint"
                in NetworkStatusHelper._network_status[interface_name]
            ):
                NetworkStatusHelper._network_status[interface_name].pop(
                    "activeaccesspoint", None
                )
            if (
                "connection_active"
                in NetworkStatusHelper._network_status[interface_name]
            ):
                NetworkStatusHelper._network_status[interface_name].pop(
                    "connection_active", None
                )
        elif new_state == int(NM.DeviceState.UNAVAILABLE):
            if "wired" in NetworkStatusHelper._network_status[interface_name]:
                NetworkStatusHelper._network_status[interface_name].pop("wired", None)
            if "wireless" in NetworkStatusHelper._network_status[interface_name]:
                NetworkStatusHelper._network_status[interface_name].pop(
                    "wireless", None
                )
        NetworkStatusHelper._network_status[interface_name]["status"][
            "State"
        ] = new_state


async def run_event_listener():

    await NetworkStatusHelper.network_status_query()

    await NetworkManagerService().add_device_added_callback(dev_added)
    await NetworkManagerService().add_device_removed_callback(dev_removed)

    # TODO:
    # with NetworkStatusHelper.get_lock():
    #     all_devices = NetworkStatusHelper.get_client().get_all_devices()
    # for dev in all_devices:
    #     if dev.get_device_type() in (
    #         NM.DeviceType.ETHERNET,
    #         NM.DeviceType.WIFI,
    #         NM.DeviceType.MODEM,
    #     ):
    #         dev.connect("state-changed", dev_statechange)
    # In case wifi connection is already activated
    # 		if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI and dev.ActiveAccessPoint:
    # 			dev.ActiveAccessPoint.OnPropertiesChanged(ap_propchange)


class NetworkStatus:
    async def start(self):
        await run_event_listener()

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 0, "InfoMsg": ""}

        try:
            await NetworkStatusHelper.network_status_query()
            result["status"] = NetworkStatusHelper._network_status

            unmanaged_devices = (
                ServerConfig()
                .get_parser()
                .get("summit-rcm", "unmanaged_hardware_devices", fallback="")
                .split()
            )
            for dev in unmanaged_devices:
                if dev in result["status"]:
                    del result["status"][dev]
            result["devices"] = len(result["status"])
            resp.media = result
        except Exception as e:
            result["InfoMsg"] = f"Could not read network status - {str(e)}"
            result["SDCERR"] = 1
            resp.media = result
