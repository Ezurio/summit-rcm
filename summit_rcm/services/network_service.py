import os
import re
from struct import pack
from subprocess import TimeoutExpired, run
from syslog import LOG_ERR, syslog
from socket import AF_INET, inet_ntop, AF_INET6
from typing import Optional, Tuple
from summit_rcm import definition
from summit_rcm.services.network_manager_service import (
    NM80211ApFlags,
    NM80211ApSecurityFlags,
    NM80211Mode,
    NMConnectivityState,
    NMDeviceCapabilities,
    NMDeviceInterfaceFlags,
    NMDeviceStateReason,
    NMDeviceType,
    NetworkManagerService,
    NMDeviceState,
    NM_SETTING_8021X_DEFAULTS,
    NM_SETTING_CONNECTION_DEFAULTS,
    NM_SETTING_IP4CONFIG_DEFAULTS,
    NM_SETTING_IP6CONFIG_DEFAULTS,
    NM_SETTING_PROXY_DEFAULTS,
    NM_SETTING_WIRED_DEFAULTS,
    NM_SETTING_WIRELESS_DEFAULTS,
    NM_SETTING_WIRELESS_SECURITY_DEFAULTS,
    NMActiveConnectionState,
)
from summit_rcm.settings import ServerConfig, SystemSettingsManage
from summit_rcm.utils import Singleton, to_camel_case

IW_PATH = "/usr/sbin/iw"


class NetworkService(metaclass=Singleton):
    @staticmethod
    async def get_dev_status(dev_properties: dict, is_legacy: bool = False) -> dict:
        """
        Retrieve device status info from the provided dev_properties dictionary
        """
        status = {}
        status["State" if is_legacy else "state"] = int(
            dev_properties.get("State", NMDeviceState.NM_DEVICE_STATE_UNKNOWN)
        )
        try:
            status[
                "StateText" if is_legacy else "stateText"
            ] = definition.SUMMIT_RCM_STATE_TEXT.get(
                status["State" if is_legacy else "state"]
            )
        except Exception:
            status["StateText" if is_legacy else "stateText"] = "Unknown"
            syslog(
                f"unknown device state value {status['State' if is_legacy else 'state']}."
                "See https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html"
            )
        status["Mtu" if is_legacy else "mtu"] = dev_properties.get("Mtu", 0)
        status["DeviceType" if is_legacy else "deviceType"] = int(
            dev_properties.get("DeviceType", NMDeviceState.NM_DEVICE_STATE_UNKNOWN)
        )
        try:
            status[
                "DeviceTypeText" if is_legacy else "deviceTypeText"
            ] = definition.SUMMIT_RCM_DEVTYPE_TEXT.get(
                status["DeviceType" if is_legacy else "deviceType"]
            )
        except Exception:
            status["DeviceTypeText" if is_legacy else "deviceTypeText"] = "Unknown"
            syslog(
                f"unknown device type value {status['DeviceType' if is_legacy else 'deviceType']}."
                "See https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html"
            )
        return status

    @staticmethod
    async def get_ip4config_properties(
        ipconfig_obj_path: str, is_legacy: bool = False
    ) -> dict:
        """
        Retrieve a dictionary of the IPv4 configuration properties (NM IP4Config) from the given
        object path
        """
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
            if is_legacy:
                ipconfig_properties["Addresses"] = addresses
            ipconfig_properties[
                "AddressData" if is_legacy else "addressData"
            ] = address_data

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
                    data["next_hop" if is_legacy else "nextHop"] = (
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
            if is_legacy:
                ipconfig_properties["Routes"] = routes
            ipconfig_properties["RouteData" if is_legacy else "routeData"] = route_data
            ipconfig_properties["Gateway" if is_legacy else "gateway"] = props.get(
                "Gateway", ""
            )
            ipconfig_properties["Domains" if is_legacy else "domains"] = []
            props_domains = (
                props["Domains"] if props.get("Domains", None) is not None else []
            )
            for domain in props_domains:
                ipconfig_properties["Domains" if is_legacy else "domains"].append(
                    domain
                )

            ipconfig_properties[
                "NameserverData" if is_legacy else "nameserverData"
            ] = []
            props_nameserver_data = (
                props["NameserverData"]
                if props.get("NameserverData", None) is not None
                else []
            )
            for nameserver in props_nameserver_data:
                nameserver["address"] = nameserver["address"].value
                ipconfig_properties[
                    "NameserverData" if is_legacy else "nameserverData"
                ].append(nameserver)
            ipconfig_properties[
                "WinsServerData" if is_legacy else "winsServerData"
            ] = []
            props_wins_server_data = (
                props["WinsServerData"]
                if props.get("WinsServerData", None) is not None
                else []
            )
            for wins_server in props_wins_server_data:
                ipconfig_properties[
                    "WinsServerData" if is_legacy else "winsServerData"
                ].append(wins_server)
        except Exception as e:
            syslog(f"Could not retrieve IPv4 configuration - {str(e)}")
            return {}

        return ipconfig_properties

    @staticmethod
    async def get_ip6config_properties(
        ipconfig_obj_path: str, is_legacy: bool = False
    ) -> dict:
        """
        Retrieve a dictionary of the IPv6 configuration properties (NM IP6Config) from the given
        object path
        """
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
            if is_legacy:
                ipconfig_properties["Addresses"] = addresses
            ipconfig_properties[
                "AddressData" if is_legacy else "addressData"
            ] = address_data

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
                    data["next_hop" if is_legacy else "nextHop"] = (
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
            if is_legacy:
                ipconfig_properties["Routes"] = routes
            ipconfig_properties["RouteData" if is_legacy else "routeData"] = route_data
            ipconfig_properties["Gateway" if is_legacy else "gateway"] = props.get(
                "Gateway", ""
            )
            ipconfig_properties["Domains" if is_legacy else "domains"] = []
            props_domains = (
                props["Domains"] if props.get("Domains", None) is not None else []
            )
            for domain in props_domains:
                ipconfig_properties["Domains" if is_legacy else "domains"].append(
                    domain
                )

            ipconfig_properties["Nameservers" if is_legacy else "nameservers"] = []
            props_nameservers = (
                props["Nameservers"]
                if props.get("Nameservers", None) is not None
                else []
            )
            for nameserver in props_nameservers:
                ipconfig_properties[
                    "Nameservers" if is_legacy else "nameservers"
                ].append(inet_ntop(AF_INET6, nameserver))
        except Exception as e:
            syslog(f"Could not retrieve IPv6 configuration - {str(e)}")
            return {}

        return ipconfig_properties

    @staticmethod
    async def get_dhcp_config_properties(
        dhcpconfig_obj_path: str, interface: str, is_legacy: bool = False
    ) -> dict:
        """
        Retrieve a dictionary of the DHCP configuration properties (IPv4 or IPv6 baed on
        'interface') from the given object path
        """
        dhcpconfig_properties = {}
        if dhcpconfig_obj_path == "":
            return dhcpconfig_properties

        try:
            props = await NetworkManagerService().get_obj_properties(
                dhcpconfig_obj_path, interface
            )

            dhcpconfig_properties["Options" if is_legacy else "options"] = {}
            options = props.get("Options", None)
            if options is not None:
                for option in options:
                    dhcpconfig_properties["Options" if is_legacy else "options"][
                        option if is_legacy else to_camel_case(option)
                    ] = options[option].value

        except Exception:
            return {}

        return dhcpconfig_properties

    @staticmethod
    async def get_dhcp4_config_properties(
        dhcpconfig_obj_path: str, is_legacy: bool = False
    ) -> dict:
        """
        Retrieve a dictionary of the IPv4 DHCP configuration properties (NM DhcpConfig) from the
        given object path
        """
        return await NetworkService.get_dhcp_config_properties(
            dhcpconfig_obj_path, NetworkManagerService().NM_DHCP4CONFIG_IFACE, is_legacy
        )

    @staticmethod
    async def get_dhcp6_config_properties(
        dhcpconfig_obj_path: str, is_legacy: bool = False
    ) -> dict:
        """
        Retrieve a dictionary of the IPv6 DHCP configuration properties (NM DhcpConfig) from the
        given object path
        """
        return await NetworkService.get_dhcp_config_properties(
            dhcpconfig_obj_path, NetworkManagerService().NM_DHCP6CONFIG_IFACE, is_legacy
        )

    @staticmethod
    async def get_wired_properties(dev_obj_path: str, is_legacy: bool = False) -> dict:
        """
        Retrieve a dictionary of properties for a wired (Ethernet) device with the provided object
        path
        """
        wired = {}
        wired_properties = await NetworkManagerService().get_obj_properties(
            dev_obj_path, NetworkManagerService().NM_DEVICE_WIRED_IFACE
        )
        wired["PermHwAddress" if is_legacy else "permHwAddress"] = wired_properties.get(
            "PermHwAddress", ""
        )
        wired["Speed" if is_legacy else "speed"] = wired_properties.get("Speed", 0)
        wired["Carrier" if is_legacy else "carrier"] = wired_properties.get(
            "Carrier", False
        )
        return wired

    @staticmethod
    async def get_wifi_properties(
        wireless_properties: dict, is_legacy: bool = False
    ) -> dict:
        """
        Retrieve a dictionary of properties for a wireless (Wi-Fi) device with the provided object
        path
        """
        wireless = {}
        wireless["Bitrate" if is_legacy else "bitrate"] = wireless_properties.get(
            "Bitrate", 0
        )
        wireless[
            "PermHwAddress" if is_legacy else "permHwAddress"
        ] = wireless_properties.get("PermHwAddress", "")
        wireless["Mode" if is_legacy else "mode"] = int(
            wireless_properties.get("Mode", NM80211Mode.NM_802_11_MODE_UNKNOWN)
        )
        wireless[
            "RegDomain" if is_legacy else "regDomain"
        ] = NetworkService.get_reg_domain_info()
        return wireless

    @staticmethod
    def get_active_ap_rssi(ifname: Optional[str] = "wlan0") -> Tuple[bool, float]:
        """
        Retrieve the signal strength in dBm for the active accesspoint on the specified interface
        (default is wlan0).

        The return value is a tuple in the form of: (success, rssi)
        """
        _RSSI_RE = r"signal: (?P<RSSI>.*) dBm"

        if not os.path.exists(IW_PATH):
            return (False, definition.INVALID_RSSI)

        try:
            proc = run(
                [IW_PATH, "dev", ifname, "link"],
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

    @staticmethod
    def get_reg_domain_info() -> str:
        """
        Retrieve the radio's regulatory domain using 'iw'
        """
        if not os.path.exists(IW_PATH):
            return "WW"

        try:
            proc = run(
                [IW_PATH, "reg", "get"],
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

    @staticmethod
    def get_frequency_info(interface: str, frequency: int) -> int:
        """
        Retrieve the current frequency used by the given 'interface' as an int using 'frequency' as
        a default
        """
        if not os.path.exists(IW_PATH):
            return frequency

        try:
            proc = run(
                [IW_PATH, "dev"],
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
                        return int(m.group(0))
        except TimeoutExpired:
            syslog(LOG_ERR, "Call 'iw dev' timeout")
        except Exception as e:
            syslog(LOG_ERR, f"Call 'iw dev' failed: {str(e)}")

        return frequency

    @staticmethod
    async def get_ap_properties(
        wireless_properties: dict, interface_name: str, is_legacy: bool = False
    ) -> dict:
        """
        Retrieve a dictionary of properties for an access point from the provided properities
        dictionary and interface name
        """
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
            ap_properties["Ssid" if is_legacy else "ssid"] = (
                ssid.decode("utf-8") if ssid is not None else ""
            )
            ap_properties["HwAddress" if is_legacy else "hwAddress"] = ap_props.get(
                "HwAddress", ""
            )
            ap_properties["Maxbitrate" if is_legacy else "maxBitrate"] = ap_props.get(
                "MaxBitrate", 0
            )
            ap_properties["Flags" if is_legacy else "flags"] = ap_props.get(
                "Flags", NM80211ApFlags.NM_802_11_AP_FLAGS_NONE
            )
            ap_properties["Wpaflags" if is_legacy else "wpaFlags"] = ap_props.get(
                "WpaFlags", NM80211ApSecurityFlags.NM_802_11_AP_SEC_NONE
            )
            ap_properties["Rsnflags" if is_legacy else "rsnFlags"] = ap_props.get(
                "RsnFlags", NM80211ApSecurityFlags.NM_802_11_AP_SEC_NONE
            )
            # Use iw dev to get channel/frequency/rssi info for AP mode
            mode = ap_props.get(
                "Mode" if is_legacy else "mode", NM80211Mode.NM_802_11_MODE_UNKNOWN
            )
            if mode == NM80211Mode.NM_802_11_MODE_AP:
                ap_properties["Strength" if is_legacy else "strength"] = 100
                ap_properties[
                    "Frequency" if is_legacy else "frequency"
                ] = NetworkService.get_frequency_info(
                    interface_name, ap_props.get("Frequency", 0)
                )
                ap_properties[
                    "Signal" if is_legacy else "signal"
                ] = definition.INVALID_RSSI
            else:
                ap_properties["Strength" if is_legacy else "strength"] = ap_props.get(
                    "Strength", 0
                )
                ap_properties["Frequency" if is_legacy else "frequency"] = ap_props.get(
                    "Frequency", 0
                )
                (success, signal) = NetworkService.get_active_ap_rssi(interface_name)
                ap_properties["Signal" if is_legacy else "signal"] = (
                    signal if success else definition.INVALID_RSSI
                )
        except Exception as e:
            syslog(f"Could not read AP properties: {str(e)}")
            return {}

        return ap_properties

    @staticmethod
    async def get_status(is_legacy: bool = False) -> dict:
        """
        Retrieve the network status information
        """
        status = {}
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
            status[interface_name] = {}

            status[interface_name]["status"] = await NetworkService.get_dev_status(
                dev_properties, is_legacy
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
                            connection_active[
                                "interface-name" if is_legacy else "interfaceName"
                            ] = (
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
                            status[interface_name][
                                "connection_active" if is_legacy else "activeConnection"
                            ] = connection_active

                status[interface_name][
                    "ip4config" if is_legacy else "ip4Config"
                ] = await NetworkService.get_ip4config_properties(
                    dev_properties.get("Ip4Config", ""), is_legacy
                )
                status[interface_name][
                    "ip6config" if is_legacy else "ip6Config"
                ] = await NetworkService.get_ip6config_properties(
                    dev_properties.get("Ip6Config", ""), is_legacy
                )
                status[interface_name][
                    "dhcp4config" if is_legacy else "dhcp4Config"
                ] = await NetworkService.get_dhcp4_config_properties(
                    dev_properties.get("Dhcp4Config", ""), is_legacy
                )
                status[interface_name][
                    "dhcp6config" if is_legacy else "dhcp6Config"
                ] = await NetworkService.get_dhcp6_config_properties(
                    dev_properties.get("Dhcp6Config", ""), is_legacy
                )

            if (
                status[interface_name]["status"].get(
                    "DeviceType" if is_legacy else "deviceType",
                    NMDeviceType.NM_DEVICE_TYPE_UNKNOWN,
                )
                == NMDeviceType.NM_DEVICE_TYPE_ETHERNET
            ):
                status[interface_name][
                    "wired"
                ] = await NetworkService.get_wired_properties(dev_obj_path, is_legacy)
                status[interface_name]["wired"][
                    "HwAddress" if is_legacy else "hwAddress"
                ] = dev_properties.get("HwAddress", "")

            if (
                status[interface_name]["status"].get(
                    "DeviceType" if is_legacy else "deviceType",
                    NMDeviceType.NM_DEVICE_TYPE_UNKNOWN,
                )
                == NMDeviceType.NM_DEVICE_TYPE_WIFI
            ):
                wireless_properties = await NetworkManagerService().get_obj_properties(
                    dev_obj_path, NetworkManagerService().NM_DEVICE_WIRELESS_IFACE
                )
                status[interface_name][
                    "wireless"
                ] = await NetworkService.get_wifi_properties(
                    wireless_properties, is_legacy
                )
                status[interface_name]["wireless"][
                    "HwAddress" if is_legacy else "hwAddress"
                ] = dev_properties.get("HwAddress", "")
                if dev_state == NMDeviceState.NM_DEVICE_STATE_ACTIVATED:
                    status[interface_name][
                        "activeaccesspoint" if is_legacy else "activeAccessPoint"
                    ] = await NetworkService.get_ap_properties(
                        wireless_properties, interface_name, is_legacy
                    )

        return status

    @staticmethod
    async def get_available_connections(dev_props: dict) -> list:
        """
        Retrieve a list of 'Connection' settings for the available connections on the given device
        """
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

    @staticmethod
    async def get_interface_status(
        target_interface_name: str, is_legacy: bool = False
    ) -> dict:
        """
        Retrieve a list of status properties for the given target interface
        """
        status = await NetworkService.get_status(is_legacy)
        if target_interface_name not in status.keys():
            return {}

        dev_properties = status[target_interface_name]
        dev_obj_paths = await NetworkManagerService().get_all_devices()
        for dev_obj_path in dev_obj_paths:
            dev_props = await NetworkManagerService().get_obj_properties(
                dev_obj_path, NetworkManagerService().NM_DEVICE_IFACE
            )
            interface_name = dev_props.get("Interface", "")
            if target_interface_name == interface_name:
                # Read all NM device properties
                dev_properties["udi"] = dev_props.get("Udi", "")
                dev_properties["path"] = dev_obj_path
                dev_properties["interface"] = interface_name
                dev_properties[
                    "ip_interface" if is_legacy else "ipInterface"
                ] = dev_props.get("IpInterface", "")
                dev_properties["driver"] = dev_props.get("Driver", "")
                dev_properties[
                    "driver_version" if is_legacy else "driverVersion"
                ] = dev_props.get("DriverVersion", "")
                dev_properties[
                    "firmware_version" if is_legacy else "firmwareVersion"
                ] = dev_props.get("FirmwareVersion", "")
                dev_properties["capabilities"] = dev_props.get(
                    "Capabilities", NMDeviceCapabilities.NM_DEVICE_CAP_NONE
                )
                state, state_reason = dev_props.get(
                    "StateReason",
                    (
                        NMDeviceState.NM_DEVICE_STATE_UNKNOWN,
                        NMDeviceStateReason.NM_DEVICE_STATE_REASON_UNKNOWN,
                    ),
                )
                dev_properties[
                    "state_reason" if is_legacy else "stateReason"
                ] = state_reason
                dev_properties[
                    "connection_active" if is_legacy else "activeConnection"
                ] = await NetworkService().get_active_connection(dev_props)
                dev_properties["managed"] = bool(dev_props.get("Managed", False))
                dev_properties["autoconnect"] = bool(
                    dev_props.get("Autoconnect", False)
                )
                dev_properties[
                    "firmware_missing" if is_legacy else "firmwareMissing"
                ] = bool(dev_props.get("FirmwareMissing", False))
                dev_properties[
                    "nm_plugin_missing" if is_legacy else "nmPluginMissing"
                ] = bool(dev_props.get("NmPluginMissing", False))
                dev_properties[
                    "available_connections" if is_legacy else "availableConnections"
                ] = await NetworkService.get_available_connections(dev_props)
                dev_properties[
                    "physical_port_id" if is_legacy else "physicalPortId"
                ] = dev_props.get("PhysicalPortId", "")
                dev_properties["metered"] = int(dev_props.get("Metered", 0))
                dev_properties[
                    "metered_text" if is_legacy else "meteredText"
                ] = definition.SUMMIT_RCM_METERED_TEXT.get(dev_properties["metered"])
                try:
                    lldp_neighbors = dev_props.get("LldpNeighbors", [])
                    lldp_neighbors = [neighbor.value for neighbor in lldp_neighbors]
                except Exception:
                    lldp_neighbors = []
                dev_properties[
                    "lldp_neighbors" if is_legacy else "lldpNeighbors"
                ] = lldp_neighbors
                dev_properties["real"] = bool(dev_props.get("Real", False))
                dev_properties[
                    "ip4connectivity" if is_legacy else "ip4Connectivity"
                ] = int(
                    dev_props.get(
                        "Ip4Connectivity",
                        NMConnectivityState.NM_CONNECTIVITY_UNKNOWN,
                    )
                )
                dev_properties[
                    "ip4connectivity_text" if is_legacy else "ip4ConnectivityText"
                ] = definition.SUMMIT_RCM_CONNECTIVITY_STATE_TEXT.get(
                    dev_properties[
                        "ip4connectivity" if is_legacy else "ip4Connectivity"
                    ]
                )
                dev_properties[
                    "ip6connectivity" if is_legacy else "ip6Connectivity"
                ] = int(
                    dev_props.get(
                        "Ip6Connectivity",
                        NMConnectivityState.NM_CONNECTIVITY_UNKNOWN,
                    )
                )
                dev_properties[
                    "ip6connectivity_text" if is_legacy else "ip6ConnectivityText"
                ] = definition.SUMMIT_RCM_CONNECTIVITY_STATE_TEXT.get(
                    dev_properties[
                        "ip6connectivity" if is_legacy else "ip6Connectivity"
                    ]
                )
                dev_properties[
                    "interface_flags" if is_legacy else "interfaceFlags"
                ] = int(
                    dev_props.get(
                        "InterfaceFlags",
                        NMDeviceInterfaceFlags.NM_DEVICE_INTERFACE_FLAG_NONE,
                    )
                )
                return dev_properties

        return {}

    @staticmethod
    async def get_all_interfaces() -> list:
        """
        Retrieve a list of the available network interfaces (including any explicitly configured as
        "managed" and excluding any explicitly configured as "unmanaged")
        """
        interfaces = []

        managed_devices = (
            ServerConfig()
            .get_parser()
            .get("summit-rcm", "managed_software_devices", fallback="")
            .split()
        )
        unmanaged_devices = (
            ServerConfig()
            .get_parser()
            .get("summit-rcm", "unmanaged_hardware_devices", fallback="")
            .split()
        )

        dev_obj_paths = await NetworkManagerService().get_all_devices()
        for dev_obj_path in dev_obj_paths:
            dev_properties = await NetworkManagerService().get_obj_properties(
                dev_obj_path, NetworkManagerService().NM_DEVICE_IFACE
            )
            # Don't return interfaces in the 'unmanated' state
            dev_state = dev_properties.get("State", None)
            if (
                dev_state is None
                or dev_state == NMDeviceState.NM_DEVICE_STATE_UNMANAGED
            ):
                continue
            interface_name = dev_properties.get("Interface", "")
            if interface_name in unmanaged_devices:
                continue
            interfaces.append(interface_name)

        if os.path.exists(definition.MODEM_ENABLE_FILE):
            for dev in managed_devices:
                if dev not in interfaces:
                    interfaces.append(dev)

        return interfaces

    @staticmethod
    async def add_virtual_interface() -> bool:
        """
        Add a virtual network interface (wlan1) using 'iw' and return a boolean indicating success.
        This is used when the radio is intended to operate in AP + STA mode. Currently, only 'wlan1'
        as a 'managed' interface is supported.
        """
        try:
            proc = run(
                [
                    IW_PATH,
                    "dev",
                    "wlan0",
                    "interface",
                    "add",
                    "wlan1",
                    "type",
                    "managed",
                ],
                timeout=SystemSettingsManage.get_user_callback_timeout(),
            )
            if not proc.returncode:
                return True
        except TimeoutExpired:
            syslog(
                LOG_ERR,
                "Call 'iw dev wlan0 interface add wlan1 type managed' timeout",
            )
        except Exception as e:
            syslog(
                LOG_ERR,
                f"Call 'iw dev wlan0 interface add wlan1 type managed' failed: {str(e)}",
            )
        return False

    @staticmethod
    async def remove_virtual_interface() -> bool:
        """
        Remove a previously-created virtual network interface (wlan1) using 'iw' and return a
        boolean indicating success. Currently, only 'wlan1' is supported.
        """
        try:
            proc = run(
                [IW_PATH, "dev", "wlan1", "del"],
                timeout=SystemSettingsManage.get_user_callback_timeout(),
            )
            if not proc.returncode:
                return True
        except TimeoutExpired:
            syslog(LOG_ERR, "Call 'iw dev wlan1 del' timeout")
        except Exception as e:
            syslog(LOG_ERR, f"Call 'iw dev wlan1 del' failed: {str(e)}")
        return False

    @staticmethod
    async def get_interface_statistics(
        target_interface_name: str, is_legacy: bool = False
    ) -> Tuple[bool, dict]:
        """
        Retrieve receive/transmit statistics for the requested interface
        """
        default_result: dict = {
            "rx_bytes" if is_legacy else "rxBytes": -1,
            "rx_packets" if is_legacy else "rxPackets": -1,
            "rx_errors" if is_legacy else "rxErrors": -1,
            "rx_dropped" if is_legacy else "rxDropped": -1,
            "multicast": -1,
            "tx_bytes" if is_legacy else "txBytes": -1,
            "tx_packets" if is_legacy else "txPackets": -1,
            "tx_errors" if is_legacy else "txErrors": -1,
            "tx_dropped" if is_legacy else "txDropped": -1,
        }

        try:
            if not target_interface_name:
                return (False, default_result)

            path_to_stats_dir = f"/sys/class/net/{target_interface_name}/statistics"
            stats_to_read = {
                "rx_bytes" if is_legacy else "rxBytes": f"{path_to_stats_dir}/rx_bytes",
                "rx_packets"
                if is_legacy
                else "rxPackets": f"{path_to_stats_dir}/rx_packets",
                "rx_errors"
                if is_legacy
                else "rxErrors": f"{path_to_stats_dir}/rx_errors",
                "rx_dropped"
                if is_legacy
                else "rxDropped": f"{path_to_stats_dir}/rx_dropped",
                "multicast": f"{path_to_stats_dir}/multicast",
                "tx_bytes" if is_legacy else "txBytes": f"{path_to_stats_dir}/tx_bytes",
                "tx_packets"
                if is_legacy
                else "txPackets": f"{path_to_stats_dir}/tx_packets",
                "tx_errors"
                if is_legacy
                else "txErrors": f"{path_to_stats_dir}/tx_errors",
                "tx_dropped"
                if is_legacy
                else "txDropped": f"{path_to_stats_dir}/tx_dropped",
            }
            output_stats: dict = {}
            for stat_name, stat_file_path in stats_to_read.items():
                with open(stat_file_path) as stat_file:
                    output_stats[stat_name] = int(stat_file.readline().strip())

            return (True, output_stats)
        except FileNotFoundError as e:
            syslog(f"Invalid interface name - {str(e)}")
        except Exception as e:
            syslog(f"Could not read interface statistics - {str(e)}")
        return (False, default_result)

    @staticmethod
    async def reload_nm_connections() -> bool:
        """
        Trigger NetworkManager to reload all connection files from disk, including noticing any
        added or deleted connection files.
        """
        return await NetworkManagerService().reload_connections()

    @classmethod
    async def get_active_connection(cls, dev_props: dict) -> dict:
        # Retrieve the active connection object path from the provided device's properties
        active_connection_obj_path = dev_props.get("ActiveConnection", None)
        if active_connection_obj_path is None:
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
                ] = NetworkService.get_reg_domain_info()

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
