import dbus
import socket, struct

result = {
    "SDCERR": 1,
}

# Standard DBUS Properties
DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"
NM_OBJ = "/org/freedesktop/NetworkManager"
NM_IFACE = "org.freedesktop.NetworkManager"
NM_DEVICE_IFACE = "org.freedesktop.NetworkManager.Device"
NM_IP4_IFACE = "org.freedesktop.NetworkManager.IP4Config"
NM_IP6_IFACE = "org.freedesktop.NetworkManager.IP6Config"
NM_DHCP4_IFACE = "org.freedesktop.NetworkManager.DHCP4Config"
NM_DHCP6_IFACE = "org.freedesktop.NetworkManager.DHCP6Config"
NM_WIRED_IFACE = "org.freedesktop.NetworkManager.Device.Wired"
NM_WIRELESS_IFACE = "org.freedesktop.NetworkManager.Device.Wireless"
NM_ACCESSPOINT_IFACE = "org.freedesktop.NetworkManager.AccessPoint"

bus = dbus.SystemBus()
proxy = bus.get_object(NM_IFACE, NM_OBJ)

# For org.freedesktop.NetworkManager
# Use standard DBUS Property on NetworkManager to
# Get NM version
manager_iface = dbus.Interface(proxy, DBUS_PROP_IFACE)

# For org.freedesktop.NetworkManager
manager = dbus.Interface(proxy, NM_IFACE)
# Call a NM_IFACE's method
devices = manager.GetDevices()
interface = {}
for d in devices:
    # Get device object
    dev_proxy = bus.get_object(NM_IFACE, d)
    prop_iface = dbus.Interface(dev_proxy, DBUS_PROP_IFACE)
    # Get org.freedesktop.NetworkManager.Device properties
    interface_name = str(prop_iface.Get(NM_DEVICE_IFACE, "Interface"))

    interface[interface_name] = {}

    # org.freedesktop.NetworkManager.Device string propertys
    interface_status = {}
    interface_status["autoconnect"] = str(
        prop_iface.Get(NM_DEVICE_IFACE, "Autoconnect")
    )
    state = prop_iface.Get(NM_DEVICE_IFACE, "State")
    interface_status["state"] = int(state)
    interface_status["mtu"] = str(prop_iface.Get(NM_DEVICE_IFACE, "Mtu"))
    device_type = prop_iface.Get(NM_DEVICE_IFACE, "DeviceType")
    interface_status["devicetype"] = int(device_type)

    # if NM_DEVICE_STATE_ACTIVATED get ipv4 address information
    if state == 100:
        # IPv4 device address information
        Ip4Config = {}
        ipv4_config_object = prop_iface.Get(NM_DEVICE_IFACE, "Ip4Config")
        ipv4_config_proxy = bus.get_object(NM_IFACE, ipv4_config_object)
        ipv4_config_iface = dbus.Interface(ipv4_config_proxy, DBUS_PROP_IFACE)
        ipv4_config_addresses = ipv4_config_iface.Get(NM_IP4_IFACE, "AddressData")
        ipv4_config_routes = ipv4_config_iface.Get(NM_IP4_IFACE, "RouteData")
        ipv4_config_gateway = ipv4_config_iface.Get(NM_IP4_IFACE, "Gateway")
        ipv4_config_domains = ipv4_config_iface.Get(NM_IP4_IFACE, "Domains")

        i = 0
        addresses = {}
        while i < len(ipv4_config_addresses):
            addresses[i] = (
                str(ipv4_config_addresses[i]["address"])
                + "/"
                + str(ipv4_config_addresses[0]["prefix"])
            )
            i += 1
        Ip4Config["address"] = addresses

        routes = {}
        i = 0
        while i < len(ipv4_config_routes):
            routes[i] = (
                str(ipv4_config_routes[i]["dest"])
                + "/"
                + str(ipv4_config_routes[0]["prefix"])
                + " metric "
                + str(ipv4_config_routes[0]["metric"])
            )
            i += 1
        Ip4Config["routes"] = routes

        Ip4Config["gateway"] = str(ipv4_config_gateway)

        i = 0
        domains = {}
        while i < len(ipv4_config_domains):
            domains[i] = str(ipv4_config_domains[i])
            i += 1
        Ip4Config["domains"] = domains

        interface[interface_name]["ip4config"] = Ip4Config

        # IPv4 lease/config information
        Dhcp4Config = {}
        ipv4_dhcp_object = prop_iface.Get(NM_DEVICE_IFACE, "Dhcp4Config")
        ipv4_dhcp_proxy = bus.get_object(NM_IFACE, ipv4_dhcp_object)
        ipv4_dhcp_iface = dbus.Interface(ipv4_dhcp_proxy, DBUS_PROP_IFACE)
        ipv4_dhcp_options = ipv4_dhcp_iface.Get(NM_DHCP4_IFACE, "Options")

        for item in ipv4_dhcp_options:
            Dhcp4Config[str(item)] = str(ipv4_dhcp_options[item])
        interface[interface_name]["dhcp4config"] = Dhcp4Config

        # IPv6 device address information
        Ip6Config = {}
        ipv6_config_object = prop_iface.Get(NM_DEVICE_IFACE, "Ip6Config")
        ipv6_config_proxy = bus.get_object(NM_IFACE, ipv6_config_object)
        ipv6_config_iface = dbus.Interface(ipv6_config_proxy, DBUS_PROP_IFACE)
        ipv6_config_addresses = ipv6_config_iface.Get(NM_IP6_IFACE, "AddressData")
        ipv6_config_routes = ipv6_config_iface.Get(NM_IP6_IFACE, "RouteData")
        ipv6_config_gateway = ipv6_config_iface.Get(NM_IP6_IFACE, "Gateway")
        ipv6_config_domains = ipv6_config_iface.Get(NM_IP6_IFACE, "Domains")

        i = 0
        addresses = {}
        while i < len(ipv6_config_addresses):
            addresses[i] = (
                str(ipv6_config_addresses[i]["address"])
                + "/"
                + str(ipv6_config_addresses[0]["prefix"])
            )
            i += 1
        Ip6Config["address"] = addresses

        i = 0
        routes = {}
        while i < len(ipv6_config_routes):
            routes[i] = (
                str(ipv6_config_routes[i]["dest"])
                + "/"
                + str(ipv6_config_routes[0]["prefix"])
                + " metric "
                + str(ipv6_config_routes[0]["metric"])
            )
            i += 1
        Ip6Config["routes"] = routes

        Ip6Config["gateway"] = str(ipv6_config_gateway)

        i = 0
        domains = {}
        while i < len(ipv6_config_domains):
            domains[i] = str(ipv6_config_domains[i])
            i += 1
        Ip4Config["domains"] = domains

        # IPv6 lease/config information
        Dhcp6Config = {}
        ipv6_dhcp_object = prop_iface.Get(NM_DEVICE_IFACE, "Dhcp6Config")
        # #Check if path is valid
        if ipv6_dhcp_object != "/":
            ipv6_dhcp_proxy = bus.get_object(NM_IFACE, ipv6_dhcp_object)
            ipv6_dhcp_iface = dbus.Interface(ipv6_dhcp_proxy, DBUS_PROP_IFACE)
            ipv6_dhcp_options = ipv6_dhcp_iface.Get(NM_DHCP6_IFACE, "Options")

            for item in ipv6_dhcp_options:
                Dhcp6Config[str(item)] = str(ipv6_dhcp_options[item])
            interface[interface_name]["dhcp6config"] = Dhcp6Config

    # Get wired specific items
    if device_type == 1:
        wired = {}
        wired_iface = dbus.Interface(dev_proxy, NM_WIRED_IFACE)
        wired_prop_iface = dbus.Interface(dev_proxy, DBUS_PROP_IFACE)
        wired_hwaddress = wired_prop_iface.Get(NM_WIRED_IFACE, "HwAddress")
        wired_permhwaddress = wired_prop_iface.Get(NM_WIRED_IFACE, "PermHwAddress")
        wired_speed = wired_prop_iface.Get(NM_WIRED_IFACE, "Speed")
        wired_carrier = wired_prop_iface.Get(NM_WIRED_IFACE, "Carrier")
        wired["hwaddress"] = str(wired_hwaddress)
        wired["permhwaddress"] = str(wired_permhwaddress)
        wired["speed"] = int(wired_speed)
        wired["carrier"] = int(wired_carrier)
        interface[interface_name]["wired"] = wired

    # Get Wifi specific items
    if device_type == 2:
        wireless = {}
        # Get a proxy for the wifi interface
        wifi_iface = dbus.Interface(dev_proxy, NM_WIRELESS_IFACE)
        wifi_prop_iface = dbus.Interface(dev_proxy, DBUS_PROP_IFACE)
        wireless_hwaddress = wifi_prop_iface.Get(NM_WIRELESS_IFACE, "HwAddress")
        wireless_permhwaddress = wifi_prop_iface.Get(NM_WIRELESS_IFACE, "PermHwAddress")
        wireless_mode = wifi_prop_iface.Get(NM_WIRELESS_IFACE, "Mode")
        wireless_bitrate = wifi_prop_iface.Get(NM_WIRELESS_IFACE, "Bitrate")
        wireless["bitrate"] = wireless_bitrate
        wireless["hwaddress"] = str(wireless_hwaddress)
        wireless["permhwaddress"] = str(wireless_permhwaddress)
        wireless["mode"] = int(wireless_mode)
        wireless["bitrate"] = int(wireless_bitrate) / 1000
        interface[interface_name]["wireless"] = wireless
        # Get all APs the card can see
        ActiveAccessPoint = {}
        active_ap = wifi_prop_iface.Get(NM_WIRELESS_IFACE, "ActiveAccessPoint")
        ap_proxy = bus.get_object(NM_IFACE, active_ap)
        ap_prop_iface = dbus.Interface(ap_proxy, DBUS_PROP_IFACE)
        ssid = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "Ssid")
        bssid = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "HwAddress")
        strength = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "Strength")
        maxbitrate = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "MaxBitrate")
        freq = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "Frequency")
        ActiveAccessPoint["ssid"] = "".join([str(v) for v in ssid])
        ActiveAccessPoint["bssid"] = str(bssid)
        ActiveAccessPoint["strength"] = int(strength)
        ActiveAccessPoint["maxbitrate"] = int(maxbitrate) / 1000
        ActiveAccessPoint["frequency"] = int(freq)
        interface[interface_name]["activeaccesspoint"] = ActiveAccessPoint

    interface[interface_name]["status"] = interface_status
    result["status"] = interface

# print(result)
for item in result["status"]:
    print(result["status"][item])
    print()
