#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
from __future__ import annotations

"""
Module to provide an interface to perform networking tasks (interfaces, connection profiles, etc.).
"""

import asyncio
import configparser
import os
from pathlib import Path
import re
from struct import pack
from syslog import LOG_ERR, syslog
from socket import AF_INET, inet_ntop, AF_INET6
import time
from typing import List, Optional, Tuple
from urllib.parse import urlparse

try:
    from dbus_fast import Message, MessageType
    from summit_rcm.dbus_manager import DBusManager
    from pyroute2.iwutil import AsyncIW
except ImportError as error:
    # Ignore the error if the pyroute2 module is not available if generating documentation
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

from summit_rcm import definition
from summit_rcm.services.network_manager_service import (
    SUMMIT_RCM_NM_ACTIVE_CONNECTION_STATE_TEXT,
    NM80211ApFlags,
    NM80211ApSecurityFlags,
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
from summit_rcm.settings import ServerConfig
from summit_rcm.utils import Singleton, frequency_to_channel, variant_to_python

RESERVED_NM_CONNECTIONS_DIR = "/usr/lib/NetworkManager/system-connections"

# See nl80211_reg_rule_flags enum from nl80211.h
NL80211_RRF_DFS = 1 << 4
NL80211_RRF_NO_IR = 1 << 7
NL80211_RRF_PASSIVE_SCAN = NL80211_RRF_NO_IR

NETWORK_STATUS_DBUS_TIMEOUT = 10.0  # seconds
"""
This constant defines the timeout duration for network status DBus requests in seconds.
"""

NETWORK_STATE_VERIFY_TIMEOUT = 3.0  # seconds
"""
Timeout for polling NetworkManager to verify a connection state change (activate, deactivate,
or wireless enable/disable) has taken effect.
"""

SUPPLICANT_INTERFACE_IFACE = "fi.w1.wpa_supplicant1.Interface"


class NetworkService(metaclass=Singleton):
    """
    Service class which provides an interface to perform networking tasks (interfaces, connection
    profiles, etc.).
    """

    @staticmethod
    def parse_rateinfo(
        rate_info: Optional[nl80211cmd.STAInfo.rate_info],
    ) -> dict | None:
        """
        Parse the rate info and return a dictionary of the parsed values
        """
        if rate_info is None:
            return None

        rate_info_dict = {
            "rate": None,
            "channelWidth": None,
        }

        if rate_info.get_attr("NL80211_RATE_INFO_BITRATE32") is not None:
            rate_info_dict["rate"] = (
                rate_info.get_attr("NL80211_RATE_INFO_BITRATE32") * 100
            )
        elif rate_info.get_attr("NL80211_RATE_INFO_BITRATE") is not None:
            rate_info_dict["rate"] = (
                rate_info.get_attr("NL80211_RATE_INFO_BITRATE") * 100
            )

        if rate_info.get_attr("NL80211_RATE_INFO_5_MHZ_WIDTH") is not None:
            rate_info_dict["channelWidth"] = 5
        elif rate_info.get_attr("NL80211_RATE_INFO_10_MHZ_WIDTH") is not None:
            rate_info_dict["channelWidth"] = 10
        elif rate_info.get_attr("NL80211_RATE_INFO_40_MHZ_WIDTH") is not None:
            rate_info_dict["channelWidth"] = 40
        elif rate_info.get_attr("NL80211_RATE_INFO_80_MHZ_WIDTH") is not None:
            rate_info_dict["channelWidth"] = 80
        elif (
            rate_info.get_attr("NL80211_RATE_INFO_80P80_MHZ_WIDTH") is not None
            or rate_info.get_attr("NL80211_RATE_INFO_160_MHZ_WIDTH") is not None
        ):
            rate_info_dict["channelWidth"] = 160
        else:
            rate_info_dict["channelWidth"] = 20

        return rate_info_dict

    @staticmethod
    def parse_bss_param(
        bss_param: Optional[nl80211cmd.STAInfo.bss_param],
    ) -> dict | None:
        """
        Parse the BSS parameter info and return a dictionary of the parsed values
        """
        if bss_param is None:
            return None

        bss_param_dict = {
            "beaconInterval": None,
            "dtimPeriod": None,
        }

        if bss_param.get_attr("NL80211_STA_BSS_PARAM_BEACON_INTERVAL") is not None:
            bss_param_dict["beaconInterval"] = bss_param.get_attr(
                "NL80211_STA_BSS_PARAM_BEACON_INTERVAL"
            )
        if bss_param.get_attr("NL80211_STA_BSS_PARAM_DTIM_PERIOD") is not None:
            bss_param_dict["dtimPeriod"] = bss_param.get_attr(
                "NL80211_STA_BSS_PARAM_DTIM_PERIOD"
            )

        return bss_param_dict

    @staticmethod
    async def get_station_dump(ifname: Optional[str] = "wlan0") -> dict:
        """
        Retrieve station dump info for the specified interface (default is wlan0)
        """
        try:
            async with AsyncIW() as iw:
                await iw.setup_endpoint()
                interfaces = await iw.get_interfaces_dump()
                try:
                    async for interface in interfaces:
                        if str(interface.get_attr("NL80211_ATTR_IFNAME")) != ifname:
                            continue

                        stations = {}
                        resp = await iw.get_stations(
                            interface.get_attr("NL80211_ATTR_IFINDEX")
                        )
                        try:
                            async for station in resp:
                                station_info = station.get_attr("NL80211_ATTR_STA_INFO")
                                if station_info is None:
                                    continue

                                bss_params = NetworkService().parse_bss_param(
                                    station_info.get_attr("NL80211_STA_INFO_BSS_PARAM")
                                )

                                stations[station.get_attr("NL80211_ATTR_MAC")] = {
                                    "signal": station_info.get_attr("NL80211_STA_INFO_SIGNAL"),
                                    "inactive": station_info.get_attr(
                                        "NL80211_STA_INFO_INACTIVE_TIME"
                                    ),
                                    "connectedTime": station_info.get_attr(
                                        "NL80211_STA_INFO_CONNECTED_TIME"
                                    ),
                                    "rxPackets": station_info.get_attr(
                                        "NL80211_STA_INFO_RX_PACKETS"
                                    ),
                                    "txPackets": station_info.get_attr(
                                        "NL80211_STA_INFO_TX_PACKETS"
                                    ),
                                    "beaconRx": station_info.get_attr(
                                        "NL80211_STA_INFO_BEACON_RX"
                                    ),
                                    "rxRate": NetworkService().parse_rateinfo(
                                        station_info.get_attr("NL80211_STA_INFO_RX_BITRATE")
                                    ),
                                    "txRate": NetworkService().parse_rateinfo(
                                        station_info.get_attr("NL80211_STA_INFO_TX_BITRATE")
                                    ),
                                    "rxBytes": station_info.get_attr(
                                        "NL80211_STA_INFO_RX_BYTES64"
                                    ),
                                    "txBytes": station_info.get_attr(
                                        "NL80211_STA_INFO_TX_BYTES64"
                                    ),
                                    "rxDuration": station_info.get_attr(
                                        "NL80211_STA_INFO_RX_DURATION"
                                    ),
                                    "txRetries": station_info.get_attr(
                                        "NL80211_STA_INFO_TX_RETRIES"
                                    ),
                                    "txFailed": station_info.get_attr(
                                        "NL80211_STA_INFO_TX_FAILED"
                                    ),
                                    "beaconLoss": station_info.get_attr(
                                        "NL80211_STA_INFO_BEACON_LOSS"
                                    ),
                                    "rxDropMisc": station_info.get_attr(
                                        "NL80211_STA_INFO_RX_DROP_MISC"
                                    ),
                                    "dtimPeriod": (
                                        bss_params["dtimPeriod"] if bss_params else None
                                    ),
                                    "beaconInterval": (
                                        bss_params["beaconInterval"] if bss_params else None
                                    ),
                                }
                        finally:
                            await resp.aclose()

                        return stations
                finally:
                    await interfaces.aclose()

            # If not found, raise exception
            raise Exception("interface not found")
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to get station dump: {str(exception)}")

        return {}

    @staticmethod
    async def get_status(is_legacy: bool = False) -> dict:
        """
        Retrieve the network status information
        """
        return NetworkManagerService().convert_property_names(
            await NetworkManagerService().get_status_internal(
                is_legacy=is_legacy,
                timeout=NETWORK_STATUS_DBUS_TIMEOUT,
            ),
            is_legacy=is_legacy,
        )

    @staticmethod
    async def get_interface_available_ap_channels(ifname: str = "wlan0") -> list:
        """
        Retrieve a list of available AP channels/frequencies for the given interface
        """
        try:
            async with AsyncIW() as iw:
                await iw.setup_endpoint()
                interfaces = await iw.get_interfaces_dump()
                try:
                    async for interface in interfaces:
                        if str(interface.get_attr("NL80211_ATTR_IFNAME")) != ifname:
                            continue

                        phy = interface.get_attr("NL80211_ATTR_WIPHY")

                        bands = None
                        wiphys = await iw.list_wiphy()
                        try:
                            async for wiphy in wiphys:
                                if wiphy.get_attr("NL80211_ATTR_WIPHY") != phy:
                                    continue
                                bands = wiphy.get_attr("NL80211_ATTR_WIPHY_BANDS")
                                break
                        finally:
                            await wiphys.aclose()

                        if not bands:
                            raise Exception("no channels found")

                        supported_channel_freqs = []
                        for band in bands:
                            for freq in band.get_attr("NL80211_BAND_ATTR_FREQS"):
                                if freq.get_attr("NL80211_FREQUENCY_ATTR_DISABLED"):
                                    continue
                                supported_channel_freqs.append(
                                    freq.get_attr("NL80211_FREQUENCY_ATTR_FREQ")
                                )

                        reg_domains = await iw.get_regulatory_domain(phy)
                        reg_domain = reg_domains[0] if reg_domains else None
                        if reg_domain is None:
                            raise Exception("no regulatory rules found")

                        for reg_rule in reg_domain.get_attr("NL80211_ATTR_REG_RULES"):
                            range_start_mhz = (
                                reg_rule.get_attr("NL80211_ATTR_FREQ_RANGE_START") / 1000
                            )
                            range_end_mhz = (
                                reg_rule.get_attr("NL80211_ATTR_FREQ_RANGE_END") / 1000
                            )
                            flags = reg_rule.get_attr("NL80211_ATTR_REG_RULE_FLAGS")
                            passive_scan = bool(flags & NL80211_RRF_PASSIVE_SCAN)
                            dfs = bool(flags & NL80211_RRF_DFS)

                            for channel_freq in supported_channel_freqs[:]:
                                if range_start_mhz <= channel_freq <= range_end_mhz and (
                                    dfs or passive_scan
                                ):
                                    supported_channel_freqs.remove(channel_freq)

                        available_channels = []
                        for channel_freq in supported_channel_freqs:
                            channel = frequency_to_channel(channel_freq)
                            available_channels.append(
                                {"channel": channel, "frequency": channel_freq}
                            )

                        return available_channels
                finally:
                    await interfaces.aclose()

            # If not found, just return an empty list
            return []
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to read channel list: {str(exception)}")
            return []

    @staticmethod
    async def get_interface_status(
        target_interface_name: str, is_legacy: bool = False
    ) -> dict:
        """
        Retrieve a list of status properties for the given target interface
        """
        return await NetworkManagerService().get_interface_status(
            target_interface_name=target_interface_name,
            is_legacy=is_legacy,
        )

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
        as a 'managed' (or 'station') interface is supported.
        """
        try:
            async with AsyncIW() as iw:
                await iw.setup_endpoint()
                await iw.add_interface(ifname="wlan1", iftype="station", phy=0)
            return True
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to add interface: {str(exception)}")
            return False

    @staticmethod
    async def remove_virtual_interface() -> bool:
        """
        Remove a previously-created virtual network interface (wlan1) using 'netlink' (pyroute2) and
        return a boolean indicating success. Currently, only 'wlan1' is supported.
        """
        try:
            async with AsyncIW() as iw:
                await iw.setup_endpoint()
                interfaces = await iw.get_interfaces_dump()
                try:
                    async for interface in interfaces:
                        if str(interface.get_attr("NL80211_ATTR_IFNAME")) != "wlan1":
                            continue

                        await iw.del_interface(interface.get_attr("NL80211_ATTR_IFINDEX"))
                        return True
                finally:
                    await interfaces.aclose()
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to del interface: {str(exception)}")
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
        except FileNotFoundError as file_not_found_error:
            syslog(f"Invalid interface name - {str(file_not_found_error)}")
        except Exception as exception:
            syslog(f"Could not read interface statistics - {str(exception)}")
        return (False, default_result)

    @staticmethod
    async def get_all_connection_profiles(is_legacy: bool = False) -> List[dict] | dict:
        """
        Retrieve a list (or dictionary if legacy support is requested) of known, valid
        NetworkManager connection profiles.
        """
        result = {}
        unmanaged_devices = (
            ServerConfig()
            .get_parser()
            .get("summit-rcm", "unmanaged_hardware_devices", fallback="")
            .split()
        )

        # Get a list of all known connections (profiles)
        settings_props = await NetworkManagerService().get_obj_properties(
            NetworkManagerService().NM_SETTINGS_OBJ_PATH,
            NetworkManagerService().NM_SETTINGS_IFACE,
        )

        connection_obj_paths = settings_props.get("Connections", [])

        manager_props = await NetworkManagerService().get_obj_properties(
            NetworkManagerService().NM_CONNECTION_MANAGER_OBJ_PATH,
            NetworkManagerService().NM_CONNECTION_MANAGER_IFACE,
        )
        active_connection_obj_paths = manager_props.get("ActiveConnections", [])

        # Loop through the connections and build a dictionary to return
        for conn in connection_obj_paths:
            try:
                connection_settings = (
                    await NetworkManagerService().get_connection_settings(conn)
                )
            except Exception as exception:
                syslog(
                    LOG_ERR,
                    f"Unable to read connection settings for {str(conn)} - {str(exception)}",
                )
                continue

            connection_settings_connection = connection_settings.get("connection", None)
            if connection_settings_connection is None:
                continue

            interface_name = (
                connection_settings_connection["interface-name"].value
                if connection_settings_connection.get("interface-name", None)
                is not None
                else ""
            )
            if unmanaged_devices and interface_name in unmanaged_devices:
                continue

            entry = {}
            entry["activated"] = False
            for active_connection in active_connection_obj_paths:
                try:
                    active_connection_props = (
                        await NetworkManagerService().get_obj_properties(
                            active_connection,
                            NetworkManagerService().NM_CONNECTION_ACTIVE_IFACE,
                        )
                    )
                except Exception as exception:
                    syslog(
                        LOG_ERR,
                        f"Unable to read properties of active connection - {str(exception)}",
                    )
                    continue
                active_connection_connection_obj_path = (
                    active_connection_props["Connection"]
                    if active_connection_props.get("Connection", None) is not None
                    else ""
                )
                if active_connection_connection_obj_path == conn:
                    entry["activated"] = (
                        active_connection_props.get("State", 0)
                        == NMActiveConnectionState.NM_ACTIVE_CONNECTION_STATE_ACTIVATED
                    )
                    break
            if is_legacy:
                # Legacy endpoints return 0 or 1 for activated
                entry["activated"] = 1 if entry["activated"] else 0
            entry["id"] = (
                connection_settings_connection["id"].value
                if connection_settings_connection.get("id", None) is not None
                else ""
            )

            # Check if the connection is an AP
            if is_legacy:
                entry["type"] = "n/a"
            else:
                entry["type"] = (
                    connection_settings_connection["type"].value
                    if connection_settings_connection.get("type", None) is not None
                    else "n/a"
                )
            try:
                connenction_settings_wireless = connection_settings.get(
                    "802-11-wireless", None
                )
                if connenction_settings_wireless is not None:
                    entry["type"] = (
                        connenction_settings_wireless["mode"].value
                        if connenction_settings_wireless.get("mode", None) is not None
                        else "infrastructure"
                    )
            except Exception as exception:
                # Couldn't read the wireless settings, so assume it's not an AP
                syslog(
                    LOG_ERR,
                    f"Unable to read connection settings wireless for {str(conn)} - "
                    f"{str(exception)}",
                )

            # Add the connection to the dictionary
            uuid = (
                connection_settings_connection["uuid"].value
                if connection_settings_connection.get("uuid", None) is not None
                else ""
            )
            result[uuid] = entry

        if is_legacy:
            return result

        # Return a list of connection profiles for non-legacy
        new_result = []
        for uuid, entry in result.items():
            new_result.append(
                {
                    "id": entry.get("id", ""),
                    "uuid": uuid,
                    "type": entry.get("type", ""),
                    "activated": entry.get("activated", 0),
                }
            )
        return new_result

    @staticmethod
    async def connection_profile_exists_by_uuid(uuid: str) -> bool:
        """Check if a connection profile with the provided UUID exists"""

        settings_props = await NetworkManagerService().get_obj_properties(
            NetworkManagerService().NM_SETTINGS_OBJ_PATH,
            NetworkManagerService().NM_SETTINGS_IFACE,
        )

        connection_obj_paths = settings_props.get("Connections", [])
        for connection_obj_path in connection_obj_paths:
            connection_props = await NetworkManagerService().get_connection_settings(
                connection_obj_path
            )

            connection_settings_connection = connection_props.get("connection", {})
            connection_uuid = (
                connection_settings_connection["uuid"].value
                if connection_settings_connection.get("uuid", None) is not None
                else ""
            )
            if uuid == connection_uuid:
                return True
        return False

    @staticmethod
    async def connection_profile_exists_by_id(id: str) -> bool:
        """Check if a connection profile with the provided id exists"""

        settings_props = await NetworkManagerService().get_obj_properties(
            NetworkManagerService().NM_SETTINGS_OBJ_PATH,
            NetworkManagerService().NM_SETTINGS_IFACE,
        )

        connection_obj_paths = settings_props.get("Connections", [])
        for connection_obj_path in connection_obj_paths:
            connection_props = await NetworkManagerService().get_connection_settings(
                connection_obj_path
            )

            connection_settings_connection = connection_props.get("connection", {})
            connection_id = (
                connection_settings_connection["id"].value
                if connection_settings_connection.get("id", None) is not None
                else ""
            )
            if id == connection_id:
                return True
        return False

    @staticmethod
    def connection_profile_is_reserved_by_uuid(uuid: str) -> bool:
        """Check if a connection profile with the provided UUID is reserved"""
        if not uuid:
            return False

        for reserved_connection_file in Path(RESERVED_NM_CONNECTIONS_DIR).iterdir():
            if reserved_connection_file.suffix != ".nmconnection":
                # Ignore any files in the directory that aren't NetworkManager connection files
                continue

            reserved_file_parser = configparser.ConfigParser()
            reserved_file_parser.read(str(reserved_connection_file))

            if str(reserved_file_parser.get("connection", "uuid", fallback="")) == uuid:
                # UUIDs match, we found a reserved connection
                return True

        return False

    @staticmethod
    def connection_profile_is_reserved_by_id(id: str) -> bool:
        """Check if a connection profile with the provided id is reserved"""
        if not id:
            return False

        for reserved_connection_file in Path(RESERVED_NM_CONNECTIONS_DIR).iterdir():
            if reserved_connection_file.suffix != ".nmconnection":
                # Ignore any files in the directory that aren't NetworkManager connection files
                continue

            if reserved_connection_file.stem == id:
                # File name 'stem' matches id, we found a reserved connection
                return True

            reserved_file_parser = configparser.ConfigParser()
            reserved_file_parser.read(str(reserved_connection_file))

            if str(reserved_file_parser.get("connection", "id", fallback="")) == id:
                # ids match, we found a reserved connection
                return True

        return False

    @staticmethod
    async def create_connection_profile(
        settings: dict,
        overwrite_existing: bool = True,
        is_legacy: bool = False,
    ) -> dict:
        """
        Create a new connection profile from the given settings (overwriting an existing connection
        profile if configured to do so) and, if successful, return the dictionary of settings for
        the newly created connection profile.
        """
        if not settings.get("connection", None):
            raise Exception("Missing connection section")

        id = settings["connection"].get("id", None)
        if not id:
            raise Exception("Missing 'id'")

        if NetworkService.connection_profile_is_reserved_by_id(id=id):
            raise ConnectionProfileReservedError("Reserved")

        if await NetworkService.connection_profile_exists_by_id(id=id):
            if not overwrite_existing:
                raise Exception(f"Connection with id '{str(id)}' already exists")

            NetworkService.delete_connection_profile(id=id)

        uuid = settings["connection"].get("uuid", None)
        if uuid is not None:
            if uuid == "":
                # NetworkManager does not like have an empty value for 'uuid' when creating a new
                # connection profile, so just remove it from the input data here
                del settings["connection"]["uuid"]
            elif await NetworkService.connection_profile_exists_by_uuid(uuid=uuid):
                if not overwrite_existing:
                    raise Exception(
                        f"Connection with UUID '{str(uuid)}' already exists"
                    )

                await NetworkService.delete_connection_profile(uuid=uuid)

        new_connection_obj_path = await NetworkManagerService().add_connection(
            await NetworkManagerService().prepare_new_connection_data(settings)
        )

        new_connection_settings_connection = (
            await NetworkManagerService().get_connection_settings(
                new_connection_obj_path
            )
        ).get("connection", {})

        new_connection_uuid = (
            new_connection_settings_connection["uuid"].value
            if new_connection_settings_connection.get("uuid", None) is not None
            else ""
        )
        if new_connection_uuid == "":
            raise ConnectionProfileNotFoundError("New connection profile not found")

        return await NetworkService.get_connection_profile_settings(
            uuid=new_connection_uuid, id=None, extended=True, is_legacy=is_legacy
        )

    @staticmethod
    async def get_connection_profile_uuid_from_id(id: str) -> str:
        """Lookup the UUID of a connection profile using the provided id (name)"""
        uuid = ""

        for entry in await NetworkService.get_all_connection_profiles(is_legacy=False):
            if entry.get("id", "") == id:
                uuid = entry.get("uuid", "")
                break

        if not uuid:
            raise ConnectionProfileNotFoundError(
                f"Connection with id '{str(id)}' not found"
            )

        return uuid

    @staticmethod
    async def get_connection_profile_id_from_uuid(uuid: str) -> str:
        """Lookup the id (name) of a connection profile using the provided UUID"""
        id = ""

        for entry in await NetworkService.get_all_connection_profiles(is_legacy=False):
            if entry.get("uuid", "") == uuid:
                id = entry.get("id", "")
                break

        if not id:
            raise ConnectionProfileNotFoundError(
                f"Connection with UUID '{str(uuid)}' not found"
            )

        return id

    @staticmethod
    async def update_connection_profile(
        new_settings: dict,
        uuid: Optional[str] = None,
        id: Optional[str] = None,
        is_legacy: bool = False,
    ) -> dict:
        """
        Update a connection profile either by UUID or by id (name) using the provided settings
        """
        if not uuid:
            if not id:
                raise ConnectionProfileNotFoundError("Invalid parameters")

            # No UUID provided, look up the connection profile by id (name)
            uuid = await NetworkService.get_connection_profile_uuid_from_id(id=id)

        activate_connection = False
        activated_setting = None
        new_settings_connection = new_settings.get("connection", None)
        if new_settings_connection:
            activated_setting = new_settings_connection.pop("activated", None)
            activate_connection = activated_setting is not None and (
                activated_setting == 1 or activated_setting == "1"
            )

        if (
            activated_setting is None
            and NetworkService.connection_profile_is_reserved_by_id(
                id
                if id
                else await NetworkService.get_connection_profile_id_from_uuid(uuid=uuid)
            )
        ):
            # If the request is not to activate/deactivate the connection (i.e., update it) and the
            # target connection is reserved, raise an error
            raise ConnectionProfileReservedError("Reserved")

        # Retrieve the current settings for the connection profile
        connection_obj_path = (
            await NetworkManagerService().get_connection_obj_path_by_uuid(uuid=uuid)
        )
        connection_settings = await NetworkManagerService().get_connection_settings(
            connection_obj_path=connection_obj_path
        )

        # Update the connection profile settings with the new, incoming ones
        connection_settings.update(
            await NetworkManagerService().prepare_new_connection_data(new_settings)
        )

        await NetworkManagerService().update_connection(
            connection_obj_path=connection_obj_path, connection=connection_settings
        )

        if activate_connection:
            # Activation requested
            await NetworkService.activate_connection_profile(uuid=uuid)

            async def _wait_activated():
                while not bool(
                    await NetworkService.get_active_connection_obj_path(uuid=uuid)
                ):
                    await asyncio.sleep(0.1)

            try:
                await asyncio.wait_for(
                    _wait_activated(), timeout=NETWORK_STATE_VERIFY_TIMEOUT
                )
            except asyncio.TimeoutError:
                raise Exception("Unable to verify connection activated")
        elif activated_setting is not None:
            # Deactivation requested
            await NetworkService.deactivate_connection_profile(uuid=uuid)

            async def _wait_deactivated():
                while bool(
                    await NetworkService.get_active_connection_obj_path(uuid=uuid)
                ):
                    await asyncio.sleep(0.1)

            try:
                await asyncio.wait_for(
                    _wait_deactivated(), timeout=NETWORK_STATE_VERIFY_TIMEOUT
                )
            except asyncio.TimeoutError:
                raise Exception("Unable to verify connection deactivated")

        return await NetworkService.get_connection_profile_settings(
            uuid=uuid, id=None, extended=True, is_legacy=is_legacy
        )

    @staticmethod
    async def delete_connection_profile(
        uuid: Optional[str] = None, id: Optional[str] = None
    ) -> None:
        """
        Delete a connection profile either by UUID or by id (name)
        """
        if not uuid:
            if not id:
                raise ConnectionProfileNotFoundError("Invalid parameters")

            # No UUID provided, look up the connection profile by id (name)
            uuid = await NetworkService.get_connection_profile_uuid_from_id(id=id)

        if NetworkService.connection_profile_is_reserved_by_id(
            id
            if id
            else await NetworkService.get_connection_profile_id_from_uuid(uuid=uuid)
        ):
            raise ConnectionProfileReservedError("Reserved")

        if not await NetworkService.connection_profile_exists_by_uuid(uuid=uuid):
            raise ConnectionProfileNotFoundError("Not found")

        connection_obj_path = (
            await NetworkManagerService().get_connection_obj_path_by_uuid(uuid=uuid)
        )

        if not connection_obj_path:
            raise ConnectionProfileNotFoundError("Not found")

        await NetworkManagerService().delete_connection(connection_obj_path)

    @staticmethod
    async def activate_connection_profile(
        uuid: Optional[str] = None, id: Optional[str] = None
    ) -> None:
        """
        Activate the connection profile with the provided UUID or id (name)
        """
        if not uuid:
            if not id:
                raise ConnectionProfileNotFoundError("Invalid parameters")

            # No UUID provided, look up the connection profile by id (name)
            uuid = await NetworkService.get_connection_profile_uuid_from_id(id=id)

        if not await NetworkService.connection_profile_exists_by_uuid(uuid=uuid):
            raise ConnectionProfileNotFoundError("Not found")

        connection_obj_path = (
            await NetworkManagerService().get_connection_obj_path_by_uuid(uuid=uuid)
        )

        if not connection_obj_path:
            raise ConnectionProfileNotFoundError("Not found")

        connection_setting_connection = (
            await NetworkManagerService().get_connection_settings(
                connection_obj_path=connection_obj_path
            )
        ).get("connection", {})

        if not connection_setting_connection.get("type", None):
            raise Exception("Unable to read connection settings")

        if connection_setting_connection["type"].value == "bridge":
            await NetworkManagerService().activate_connection(
                connection_obj_path, "/", "/"
            )
            return

        interface_name = (
            connection_setting_connection["interface-name"].value
            if connection_setting_connection.get("interface-name", None) is not None
            else ""
        )
        if not interface_name:
            raise Exception("Could not find valid interface for the connection profile")

        all_devices = await NetworkManagerService().get_all_devices()
        for dev_obj_path in all_devices:
            dev_props = await NetworkManagerService().get_obj_properties(
                dev_obj_path,
                NetworkManagerService().NM_DEVICE_IFACE,
            )

            dev_interface_name = dev_props.get("Interface", None)
            if not dev_interface_name:
                continue

            if dev_interface_name == interface_name:
                await NetworkManagerService().activate_connection(
                    connection_obj_path, dev_obj_path, "/"
                )
                return

        raise Exception("Appropriate device not found")

    @staticmethod
    async def deactivate_connection_profile(
        uuid: Optional[str] = None, id: Optional[str] = None
    ) -> None:
        """
        Deactivate the connection profile with the provided UUID or id (name)
        """
        if not uuid:
            if not id:
                raise ConnectionProfileNotFoundError("Invalid parameters")

            # No UUID provided, look up the connection profile by id (name)
            uuid = await NetworkService.get_connection_profile_uuid_from_id(id=id)

        active_connection_obj_path = (
            await NetworkService.get_active_connection_obj_path(uuid=uuid)
        )
        if not active_connection_obj_path:
            raise ConnectionProfileAlreadyInactiveError(
                "Connection was already inactive"
            )

        await NetworkManagerService().deactivate_connection(
            active_connection=active_connection_obj_path
        )

    @staticmethod
    async def get_active_connection_obj_path(uuid: str) -> str:
        """
        Return the object path of the ActiveConnection if the connection profile with the provided
        UUID is activated; otherwise, return an empty string.
        """
        manager_props = await NetworkManagerService().get_obj_properties(
            NetworkManagerService().NM_CONNECTION_MANAGER_OBJ_PATH,
            NetworkManagerService().NM_CONNECTION_MANAGER_IFACE,
        )
        active_connection_obj_paths = manager_props.get("ActiveConnections", [])

        for active_connection_obj_path in active_connection_obj_paths:
            try:
                active_connection_props = (
                    await NetworkManagerService().get_obj_properties(
                        active_connection_obj_path,
                        NetworkManagerService().NM_CONNECTION_ACTIVE_IFACE,
                    )
                )
            except Exception:
                # Unable to retrieve properties for the 'ActiveConnection' with an object path of
                # 'active_connection_obj_path', which means this connection is no longer active. So,
                # just continue through the loop.
                continue

            active_connection_uuid = active_connection_props.get("Uuid", None)
            if not active_connection_uuid:
                continue

            if uuid == active_connection_uuid:
                return active_connection_obj_path

        return ""

    @staticmethod
    def cert_to_filename(cert: bytearray | list) -> Optional[str]:
        """
        Return base name only.
        """
        try:
            if not cert:
                return None

            if isinstance(cert, list):
                cert = bytearray(cert)
            elif not isinstance(cert, bytearray):
                raise Exception("Invalid type")

            return Path(urlparse(cert.split(b"\0")[0].decode("utf-8")).path).name
        except Exception as exception:
            syslog(LOG_ERR, f"Could not decode certificate filename: {exception}")
            return None

    @staticmethod
    async def get_connection_profile_settings(
        uuid: Optional[str] = None,
        id: Optional[str] = None,
        extended: bool = True,
        is_legacy: bool = False,
    ) -> dict:
        """
        Retrieve the settings configuration of a connection profile identified by either the
        provided UUID or id (name). Passing 'extended' as False returns a limited set of the
        connection profile's settings (this was the legacy behavior).
        """
        if not uuid:
            if not id:
                raise ConnectionProfileNotFoundError("Invalid parameters")

            # No UUID provided, look up the connection profile by id (name)
            uuid = await NetworkService.get_connection_profile_uuid_from_id(id=id)

        if extended:
            settings = await NetworkService.get_extended_connection_settings(
                uuid=uuid, is_legacy=is_legacy
            )
            settings.update(
                {
                    "activated": bool(
                        await NetworkService.get_active_connection_obj_path(uuid=uuid)
                    )
                }
            )
            return settings

        # Get a list of all known connections (profiles)
        settings_props = await NetworkManagerService().get_obj_properties(
            NetworkManagerService().NM_SETTINGS_OBJ_PATH,
            NetworkManagerService().NM_SETTINGS_IFACE,
        )

        connection_obj_paths = settings_props.get("Connections", [])
        for connection_obj_path in connection_obj_paths:
            settings = await NetworkManagerService().get_connection_settings(
                connection_obj_path
            )
            connection_uuid = settings.get("connection", {}).get("uuid", None)
            if connection_uuid is not None and connection_uuid.value == uuid:
                for setting in settings:
                    properties_to_delete = []
                    for property in settings[setting]:
                        # Handle SSID special case
                        if setting == "802-11-wireless" and property == "ssid":
                            settings[setting][property] = bytearray(
                                settings[setting][property].value
                            ).decode("utf-8")
                            continue

                        # Handle cert special cases
                        if setting == "802-1x" and property in [
                            "ca-cert",
                            "client-cert",
                            "private-key",
                            "phase2-ca-cert",
                            "phase2-client-cert",
                            "phase2-private-key",
                        ]:
                            settings[setting][
                                property
                            ] = NetworkService.cert_to_filename(
                                settings[setting][property].value
                            )
                            continue

                        # Handle ip config special cases
                        if setting in ["ipv4", "ipv6"]:
                            # Handle ipv6.dns special case - its value type is array of byte array.
                            # ipv6.dns is marked as deprecated (in favor of ipv6.dns-data); however,
                            # we still need to support it for backward compatibility.
                            # https://networkmanager.dev/docs/api/latest/nm-settings-dbus.html#id-1.2.9.4.20
                            if setting == "ipv6" and property == "dns":
                                new_dns = []
                                for dns_value in settings[setting][property].value:
                                    try:
                                        dns_value = inet_ntop(AF_INET6, dns_value)
                                    except Exception:
                                        pass
                                    new_dns.append(str(dns_value))
                                settings[setting][property] = new_dns
                                continue
                            # Handle address-data special case
                            if property == "address-data":
                                address_data = settings[setting][property].value
                                for addr in address_data:
                                    addr["address"] = addr["address"].value
                                    addr["prefix"] = addr["prefix"].value
                                settings[setting][property] = address_data
                                continue

                            # Handle route-data special case
                            if property == "route-data":
                                route_data = settings[setting][property].value
                                for route in route_data:
                                    route["dest"] = route["dest"].value
                                    route["prefix"] = route["prefix"].value
                                    route["next-hop"] = (
                                        route["next-hop"].value
                                        if route.get("next-hop", None) is not None
                                        else None
                                    )
                                    route["metric"] = (
                                        route["metric"].value
                                        if route.get("metric", None) is not None
                                        else -1
                                    )
                                settings[setting][property] = route_data
                                continue

                            # Handle addresses and routes special cases (these properties are
                            # deprecated)
                            if property in ["addresses", "routes"]:
                                properties_to_delete.append(property)
                                continue

                        settings[setting][property] = settings[setting][property].value

                    # Remove properties marked for deletion (deprecated properties)
                    for property in properties_to_delete:
                        del settings[setting][property]

                settings.update(
                    {
                        "activated": bool(
                            await NetworkService.get_active_connection_obj_path(
                                uuid=uuid
                            )
                        )
                    }
                )
                return settings

        raise ConnectionProfileNotFoundError("Invalid parameters")

    @staticmethod
    async def extract_general_properties_from_active_connection(
        active_connection_props: dict, is_legacy: bool = False
    ) -> dict:
        """Retrieve the 'GENERAL' properties from the provided 'ActiveConnection' properties"""
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
            device["ip-interface" if is_legacy else "ipInterface"] = device_props.get(
                "IpInterface", None
            )
            properties["devices"].append(device)

        properties["state"] = SUMMIT_RCM_NM_ACTIVE_CONNECTION_STATE_TEXT.get(
            active_connection_props.get(
                "State", NMActiveConnectionState.NM_ACTIVE_CONNECTION_STATE_UNKNOWN
            )
        )

        properties["default"] = active_connection_props.get("Default", False)
        properties["default6"] = active_connection_props.get("Default6", False)
        properties[
            "specific-object-path" if is_legacy else "specificObjectPath"
        ] = active_connection_props.get("SpecificObject", None)
        properties["vpn"] = active_connection_props.get("Vpn", False)

        connection_obj_path = active_connection_props.get("Connection", "")
        properties["con-path" if is_legacy else "conPath"] = connection_obj_path
        connection_conn_props = await NetworkManagerService().get_connection_settings(
            connection_obj_path
        )
        connection_setting_connection = connection_conn_props.get("connection", None)
        properties["zone"] = (
            connection_setting_connection["zone"].value
            if connection_setting_connection
            and connection_setting_connection.get("zone", None)
            else None
        )

        properties[
            "master-path" if is_legacy else "masterPath"
        ] = active_connection_props.get("Master", None)

        return properties

    @staticmethod
    async def extract_ip4_config_properties_from_active_connection(
        active_connection_props: dict, is_legacy: bool = False
    ) -> dict:
        """Retrieve the 'IP4' properties from the provided 'ActiveConnection' properties"""
        return await NetworkService.extract_ip_config_properties_from_active_connection(
            active_connection_props=active_connection_props,
            is_ipv4=True,
            is_legacy=is_legacy,
        )

    @staticmethod
    async def extract_ip6_config_properties_from_active_connection(
        active_connection_props: dict, is_legacy: bool = False
    ) -> dict:
        """Retrieve the 'IP6' properties from the provided 'ActiveConnection' properties"""
        return await NetworkService.extract_ip_config_properties_from_active_connection(
            active_connection_props=active_connection_props,
            is_ipv4=False,
            is_legacy=is_legacy,
        )

    @staticmethod
    async def extract_ip_config_properties_from_active_connection(
        active_connection_props: dict, is_ipv4: bool = True, is_legacy: bool = False
    ) -> dict:
        """
        Retrieve the ipconfig properties (v4 or v6) from the provided 'ActiveConnection'
        properties
        """
        # Attempt to match output from:
        # 'nmcli connection show <target_profile>'
        properties = {
            "address-data" if is_legacy else "addressData": [],
            "domains": [],
            "gateway": None,
            "dns": [],
            "route-data" if is_legacy else "routeData": [],
        }
        if is_legacy:
            # Only include 'addresses' and 'routes' for legacy purposes
            properties.update({"addresses": [], "routes": []})

        ipconfig_obj_path = active_connection_props.get(
            "Ip4Config" if is_ipv4 else "Ip6Config", None
        )
        if ipconfig_obj_path is None or ipconfig_obj_path == "/":
            return properties

        ipconfig_props = await NetworkManagerService().get_obj_properties(
            ipconfig_obj_path,
            NetworkManagerService().NM_IP4CONFIG_IFACE
            if is_ipv4
            else NetworkManagerService().NM_IP6CONFIG_IFACE,
        )

        for address in ipconfig_props.get("AddressData", []):
            try:
                if is_legacy:
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
                properties["address-data" if is_legacy else "addressData"].append(
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

        nameservers = ipconfig_props.get("Nameservers", [])
        for nameserver in nameservers:
            properties["dns"].append(
                inet_ntop(
                    AF_INET if is_ipv4 else AF_INET6,
                    pack("L", nameserver) if is_ipv4 else nameserver,
                )
            )

        for route in ipconfig_props.get("RouteData", []):
            try:
                if is_legacy:
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
                properties["route-data" if is_legacy else "routeData"].append(
                    {
                        "dest": route["dest"].value
                        if route.get("dest", None) is not None
                        else "",
                        "prefix": route["prefix"].value
                        if route.get("prefix", None) is not None
                        else 0,
                        "next-hop"
                        if is_legacy
                        else "nextHop": route["next-hop"].value
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

    @staticmethod
    async def extract_dhcp4_config_properties_from_active_connection(
        active_connection_props: dict, is_legacy: bool = False
    ) -> dict:
        """Retrieve the 'DHCP4' properties from the provided 'ActiveConnection' properties"""
        return (
            await NetworkService.extract_dhcp_config_properties_from_active_connection(
                active_connection_props=active_connection_props,
                is_ipv4=True,
                is_legacy=is_legacy,
            )
        )

    @staticmethod
    async def extract_dhcp6_config_properties_from_active_connection(
        active_connection_props: dict, is_legacy: bool = False
    ) -> dict:
        """Retrieve the 'DHCP6' properties from the provided 'ActiveConnection' properties"""
        return (
            await NetworkService.extract_dhcp_config_properties_from_active_connection(
                active_connection_props=active_connection_props,
                is_ipv4=False,
                is_legacy=is_legacy,
            )
        )

    @staticmethod
    async def extract_dhcp_config_properties_from_active_connection(
        active_connection_props: dict, is_ipv4: bool = True, is_legacy: bool = False
    ) -> dict:
        """
        Retrieve the DHCP config properties (v4 or v6) from the provided 'ActiveConnection'
        properties
        """
        # Attempt to match output from:
        # 'nmcli connection show <target_profile>'
        properties = {"options": {} if is_legacy else []}

        dhcpconfig_obj_path = active_connection_props.get(
            "Dhcp4Config" if is_ipv4 else "Dhcp6Config", None
        )
        if dhcpconfig_obj_path is None or dhcpconfig_obj_path == "/":
            return properties

        try:
            dhcpconfig_props = await NetworkManagerService().get_obj_properties(
                dhcpconfig_obj_path,
                NetworkManagerService().NM_DHCP4CONFIG_IFACE
                if is_ipv4
                else NetworkManagerService().NM_DHCP6CONFIG_IFACE,
            )

            for option in dhcpconfig_props.get("Options", []):
                if is_legacy:
                    properties["options"][option] = properties["options"][option].value
                else:
                    properties["options"].append(
                        {
                            "option": option,
                            "value": properties["options"][option].value,
                        }
                    )
        except Exception:
            return {"options": {} if is_legacy else []}

        return properties

    @staticmethod
    async def get_extended_connection_settings(
        uuid: str, is_legacy: bool = False
    ) -> dict:
        """
        Retrieve an extended dictionary of settings for the connection profile with the provided
        UUID.
        """
        if not uuid or uuid == "":
            raise Exception("Invalid UUID")

        if not await NetworkService.connection_profile_exists_by_uuid(uuid=uuid):
            raise ConnectionProfileNotFoundError(
                f"Invalid UUID - connection with UUID '{str(uuid)}' not found"
            )

        settings = {}

        try:
            connection_obj_path = (
                await NetworkManagerService().get_connection_obj_path_by_uuid(str(uuid))
            )
        except Exception as exception:
            raise Exception(f"Invalid UUID - {str(exception)}")

        if connection_obj_path == "":
            raise Exception("Invalid UUID")

        connection_conn_props = await NetworkManagerService().get_connection_settings(
            connection_obj_path
        )

        # 'connection' setting
        settings["connection"] = NM_SETTING_CONNECTION_DEFAULTS.copy()
        setting_connection = connection_conn_props.get("connection", None)
        if setting_connection is not None:
            for param in setting_connection:
                settings["connection"][param] = setting_connection[param].value

        # 'ipv4' setting
        settings["ipv4"] = NM_SETTING_IP4CONFIG_DEFAULTS.copy()
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
        settings["ipv6"] = NM_SETTING_IP6CONFIG_DEFAULTS.copy()
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
        settings["proxy"] = NM_SETTING_PROXY_DEFAULTS.copy()
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
                ] = await NetworkService.extract_general_properties_from_active_connection(
                    active_connection_props=active_connection_props, is_legacy=is_legacy
                )
                settings["GENERAL"]["dbus-path"] = active_connection_obj_path
                settings[
                    "IP4"
                ] = await NetworkService.extract_ip4_config_properties_from_active_connection(
                    active_connection_props=active_connection_props, is_legacy=is_legacy
                )
                settings[
                    "IP6"
                ] = await NetworkService.extract_ip6_config_properties_from_active_connection(
                    active_connection_props=active_connection_props, is_legacy=is_legacy
                )
                settings[
                    "DHCP4"
                ] = await NetworkService.extract_dhcp4_config_properties_from_active_connection(
                    active_connection_props=active_connection_props, is_legacy=is_legacy
                )
                settings[
                    "DHCP6"
                ] = await NetworkService.extract_dhcp6_config_properties_from_active_connection(
                    active_connection_props=active_connection_props, is_legacy=is_legacy
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
                ] = NM_SETTING_WIRED_DEFAULTS.copy()
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
                ] = NM_SETTING_WIRELESS_DEFAULTS.copy()
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
                ] = await NetworkManagerService.get_reg_domain_info()

                settings[
                    definition.SUMMIT_RCM_NM_SETTING_WIRELESS_SECURITY_TEXT
                ] = NM_SETTING_WIRELESS_SECURITY_DEFAULTS.copy()
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
                ] = NM_SETTING_8021X_DEFAULTS.copy()
                for param in setting_8021x:
                    # The following properties are presented as a bytearray containing "file://"
                    # followed by the path to the target file and a terminating null byte
                    # See below for more info:
                    # https://lazka.github.io/pgi-docs/#NM-1.0/classes/Setting8021x.html#NM.Setting8021x.props.ca_cert
                    if param in [
                        "ca-cert",
                        "client-cert",
                        "phase2-ca-cert",
                        "phase2-client-cert",
                        "phase2-private-key",
                        "private-key",
                    ]:
                        settings[definition.SUMMIT_RCM_NM_SETTING_802_1X_TEXT][
                            param
                        ] = NetworkService.cert_to_filename(setting_8021x[param].value)
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

        return settings

    @staticmethod
    def get_access_point_security_description(
        flags: int, wpa_flags: int, rsn_flags: int
    ) -> Tuple[str, str]:
        """Analyze the provided AP flags and return the security and key management supported"""

        security_string = ""
        keymgmt = ""
        if (
            flags & NM80211ApFlags.NM_802_11_AP_FLAGS_PRIVACY
            and wpa_flags == NM80211ApSecurityFlags.NM_802_11_AP_SEC_NONE
            and rsn_flags == NM80211ApSecurityFlags.NM_802_11_AP_SEC_NONE
        ):
            # WEP
            security_string += "WEP "
            keymgmt = "static"
        else:
            if wpa_flags != NM80211ApSecurityFlags.NM_802_11_AP_SEC_NONE:
                # WPA1
                security_string += "WPA1 "

            if (
                (rsn_flags & NM80211ApSecurityFlags.NM_802_11_AP_SEC_KEY_MGMT_PSK)
                or (rsn_flags & NM80211ApSecurityFlags.NM_802_11_AP_SEC_KEY_MGMT_CCKM)
                or (
                    rsn_flags & NM80211ApSecurityFlags.NM_802_11_AP_SEC_KEY_MGMT_SUITE_B
                )
                or (rsn_flags & NM80211ApSecurityFlags.NM_802_11_AP_SEC_KEY_MGMT_802_1X)
            ):
                # WPA2
                security_string += "WPA2 "

            if rsn_flags & NM80211ApSecurityFlags.NM_802_11_AP_SEC_KEY_MGMT_SAE:
                # WPA3
                security_string += "WPA3 "
                keymgmt += "sae "

            if (wpa_flags == NM80211ApSecurityFlags.NM_802_11_AP_SEC_NONE) and (
                rsn_flags
                == (
                    NM80211ApSecurityFlags.NM_802_11_AP_SEC_KEY_MGMT_EAP_SUITE_B_192
                    | NM80211ApSecurityFlags.NM_802_11_AP_SEC_PAIR_GCMP_256
                    | NM80211ApSecurityFlags.NM_802_11_AP_SEC_GROUP_GCMP_256
                    | NM80211ApSecurityFlags.NM_802_11_AP_SEC_MGMT_GROUP_GMAC_256
                )
            ):
                # WPA3
                security_string += "WPA3 "
                keymgmt = "wpa-eap-suite-b-192"

            if rsn_flags & NM80211ApSecurityFlags.NM_802_11_AP_SEC_KEY_MGMT_OWE != 0:
                # OWE
                security_string += "OWE "
                keymgmt = "owe"
            elif (
                rsn_flags & NM80211ApSecurityFlags.NM_802_11_AP_SEC_KEY_MGMT_OWE_TM != 0
            ):
                # OWE-TM
                security_string += "OWE-TM "
                keymgmt = "owe"

            if (
                (wpa_flags & NM80211ApSecurityFlags.NM_802_11_AP_SEC_KEY_MGMT_802_1X)
                or (rsn_flags & NM80211ApSecurityFlags.NM_802_11_AP_SEC_KEY_MGMT_CCKM)
                or (
                    rsn_flags & NM80211ApSecurityFlags.NM_802_11_AP_SEC_KEY_MGMT_SUITE_B
                )
                or (rsn_flags & NM80211ApSecurityFlags.NM_802_11_AP_SEC_KEY_MGMT_802_1X)
            ):
                # 802.1X
                security_string += "802.1X "
                if rsn_flags & NM80211ApSecurityFlags.NM_802_11_AP_SEC_KEY_MGMT_SUITE_B:
                    keymgmt += "wpa-eap-suite-b "
                else:
                    keymgmt += "wpa-eap "

            if (
                wpa_flags
                & NM80211ApSecurityFlags.NM_802_11_AP_SEC_KEY_MGMT_EAP_SUITE_B_192
            ) or (
                rsn_flags
                & NM80211ApSecurityFlags.NM_802_11_AP_SEC_KEY_MGMT_EAP_SUITE_B_192
            ):
                # WPA-EAP-SUITE-B-192
                security_string += "WPA-EAP-SUITE-B-192 "
                keymgmt += "wpa-eap-suite-b-192 "

            if (wpa_flags & NM80211ApSecurityFlags.NM_802_11_AP_SEC_KEY_MGMT_PSK) or (
                rsn_flags & NM80211ApSecurityFlags.NM_802_11_AP_SEC_KEY_MGMT_PSK
            ):
                # PSK
                security_string += "PSK "
                keymgmt += "wpa-psk "

        if not keymgmt:
            # Open
            keymgmt = "none"

        return security_string.rstrip(" "), keymgmt.rstrip(" ")

    @staticmethod
    async def get_seconds_since_last_scan() -> int:
        """
        Retrieve the number of seconds since the last Wi-Fi scan was performed or -1 if no Wi-Fi
        devices were found or no scans have been performed yet.
        """
        dev_obj_paths = await NetworkManagerService().get_all_devices()
        for dev_obj_path in dev_obj_paths:
            dev_properties = await NetworkManagerService().get_obj_properties(
                dev_obj_path, NetworkManagerService().NM_DEVICE_IFACE
            )
            if (
                dev_properties.get("DeviceType", NMDeviceType.NM_DEVICE_TYPE_UNKNOWN)
                == NMDeviceType.NM_DEVICE_TYPE_WIFI
            ):
                wireless_properties = await NetworkManagerService().get_obj_properties(
                    dev_obj_path,
                    NetworkManagerService().NM_DEVICE_WIRELESS_IFACE,
                )
                last_scan = wireless_properties.get("LastScan", -1)
                return (
                    int(time.clock_gettime(time.CLOCK_BOOTTIME) - (last_scan / 1000))
                    if last_scan != -1
                    else -1
                )

        # No Wi-Fi devices found, return -1
        return -1

    @staticmethod
    async def get_access_points(is_legacy: bool = False) -> list:
        """
        Retrieve a list of info on the cached APs know to NetworkManager
        """
        access_points = []
        dev_obj_paths = await NetworkManagerService().get_all_devices()
        for dev_obj_path in dev_obj_paths:
            dev_properties = await NetworkManagerService().get_obj_properties(
                dev_obj_path, NetworkManagerService().NM_DEVICE_IFACE
            )
            if (
                dev_properties.get("DeviceType", NMDeviceType.NM_DEVICE_TYPE_UNKNOWN)
                == NMDeviceType.NM_DEVICE_TYPE_WIFI
            ):
                wireless_properties = await NetworkManagerService().get_obj_properties(
                    dev_obj_path,
                    NetworkManagerService().NM_DEVICE_WIRELESS_IFACE,
                )
                for ap_obj_path in wireless_properties.get("AccessPoints", []):
                    ap = await NetworkManagerService().get_obj_properties(
                        ap_obj_path,
                        NetworkManagerService().NM_ACCESS_POINT_IFACE,
                    )
                    flags = ap.get("Flags", NM80211ApFlags.NM_802_11_AP_FLAGS_NONE)
                    wpa_flags = ap.get(
                        "WpaFlags", NM80211ApSecurityFlags.NM_802_11_AP_SEC_NONE
                    )
                    rsn_flags = ap.get(
                        "RsnFlags", NM80211ApSecurityFlags.NM_802_11_AP_SEC_NONE
                    )
                    (
                        security_string,
                        keymgmt,
                    ) = NetworkService.get_access_point_security_description(
                        flags=flags, wpa_flags=wpa_flags, rsn_flags=rsn_flags
                    )
                    ssid = ap.get("Ssid", None)
                    ap_data = {}
                    ap_data["SSID" if is_legacy else "ssid"] = (
                        ssid.decode("utf-8") if ssid is not None else ""
                    )
                    ap_data["HwAddress" if is_legacy else "hwAddress"] = ap.get(
                        "HwAddress", ""
                    )
                    ap_data["Strength" if is_legacy else "strength"] = ap.get(
                        "Strength", 0
                    )
                    ap_data["MaxBitrate" if is_legacy else "maxBitrate"] = ap.get(
                        "MaxBitrate", 0
                    )
                    ap_data["Frequency" if is_legacy else "frequency"] = ap.get(
                        "Frequency", 0
                    )
                    ap_data["Flags" if is_legacy else "flags"] = flags
                    ap_data["WpaFlags" if is_legacy else "wpaFlags"] = wpa_flags
                    ap_data["RsnFlags" if is_legacy else "rsnFlags"] = rsn_flags
                    ap_data["LastSeen" if is_legacy else "lastSeen"] = ap.get(
                        "LastSeen", -1
                    )
                    ap_data["Security" if is_legacy else "security"] = security_string
                    ap_data["Keymgmt" if is_legacy else "keymgmt"] = keymgmt
                    access_points.append(ap_data)
        return access_points

    @staticmethod
    async def request_ap_scan():
        """Request NetworkManager to perform an access point scan"""
        dev_obj_paths = await NetworkManagerService().get_all_devices()
        for dev_obj_path in dev_obj_paths:
            dev_properties = await NetworkManagerService().get_obj_properties(
                dev_obj_path, NetworkManagerService().NM_DEVICE_IFACE
            )
            if (
                dev_properties.get("DeviceType", NMDeviceType.NM_DEVICE_TYPE_UNKNOWN)
                == NMDeviceType.NM_DEVICE_TYPE_WIFI
            ):
                await NetworkManagerService().wifi_device_request_scan(dev_obj_path, {})
                return

        raise WifiDeviceNotFoundError("Wi-Fi interface not found")

    @staticmethod
    async def get_wireless_enabled() -> bool:
        """Retrieve whether or not wireless (Wi-Fi) is enabled in NetworkManager"""
        connection_manager_props = await NetworkManagerService().get_obj_properties(
            NetworkManagerService().NM_CONNECTION_MANAGER_OBJ_PATH,
            NetworkManagerService().NM_CONNECTION_MANAGER_IFACE,
        )
        result = connection_manager_props.get("WirelessEnabled", None)
        if result is None:
            raise Exception("Unable to read NM properties")

        return result

    @staticmethod
    async def set_wireless_enabled(enabled: bool, verify: bool = True):
        """Set whether or not wireless (Wi-Fi) is enabled in NetworkManager"""
        await NetworkManagerService().set_obj_properties(
            NetworkManagerService().NM_CONNECTION_MANAGER_OBJ_PATH,
            NetworkManagerService().NM_CONNECTION_MANAGER_IFACE,
            "WirelessEnabled",
            enabled,
            "b",
        )
        if not verify:
            return

        async def _wait_wireless_state():
            while await NetworkService.get_wireless_enabled() != enabled:
                await asyncio.sleep(0.1)

        try:
            await asyncio.wait_for(
                _wait_wireless_state(), timeout=NETWORK_STATE_VERIFY_TIMEOUT
            )
        except asyncio.TimeoutError:
            raise Exception(
                f"Unable to verify wireless {'enabled' if enabled else 'disabled'}"
            )

    @staticmethod
    async def get_wireless_hardware_enabled() -> bool:
        """
        Retrieve whether or not wireless (Wi-Fi) hardware is enabled in NetworkManager, i.e. the
        state of the RF kill switch.
        """
        connection_manager_props = await NetworkManagerService().get_obj_properties(
            NetworkManagerService().NM_CONNECTION_MANAGER_OBJ_PATH,
            NetworkManagerService().NM_CONNECTION_MANAGER_IFACE,
        )
        result = connection_manager_props.get("WirelessHardwareEnabled", None)
        if result is None:
            raise Exception("Unable to read NM properties")

        return result

    @staticmethod
    async def get_interface_driver_info(name: str) -> dict:
        """
        Retrieve driver info for the requested interface
        """
        result = {
            "adoptedCountryCode": "",
            "otpCountryCode": "",
        }

        if not name:
            raise FileNotFoundError("No interface name provided")

        driver_country_code_sysfs_file = f"/sys/class/net/{name}/phy80211/device/lrd/cc"

        if os.path.exists(driver_country_code_sysfs_file):
            # The country code sysfs file returns the adopted setting when a 0 is written to it and
            # returns the OTP setting when a 1 is written to it
            with open(driver_country_code_sysfs_file, "w") as f:
                f.write("0")
            with open(driver_country_code_sysfs_file, "r") as f:
                result["adoptedCountryCode"] = f.read().strip()

            with open(driver_country_code_sysfs_file, "w") as f:
                f.write("1")
            with open(driver_country_code_sysfs_file, "r") as f:
                result["otpCountryCode"] = f.read().strip()

            return result

        driver_info = ""
        with open(f"/sys/class/net/{name}/phy80211/device/lrd/info") as f:
            driver_info = f.read()

        if driver_info:
            # Find country code info
            match = re.search(
                r".*Country code\s*: '(?P<ADOPTED>.*)'\s*\('(?P<OTP>.*)'\)",
                driver_info,
            )
            if match:
                result["adoptedCountryCode"] = str(match.group("ADOPTED"))
                result["otpCountryCode"] = str(match.group("OTP"))
                return result

        raise Exception("Unable to retrieve driver info")

    @staticmethod
    def get_dhcp_leases(name: str) -> dict:
        """
        Retrieve DHCP leases for the requested interface
        """
        if not name:
            raise FileNotFoundError("No interface name provided")

        name = Path(name).name
        result = {
            "ipv4": [],
            "ipv6": [],
        }

        if not os.path.exists(f"/var/lib/NetworkManager/dnsmasq-{name}.leases"):
            raise FileNotFoundError("Invalid interface name")
        with open(
            f"/var/lib/NetworkManager/dnsmasq-{name}.leases", encoding="utf-8"
        ) as leases_file:
            for line in leases_file:
                elements = line.split()

                # dnsmasq stores the DHCPv6 DUID in the leasefile, so we need to ignore entries with
                # fewer than 5 elements when parsing.
                #
                # See the "--dhcp-duid" option here:
                # https://thekelleys.org.uk/dnsmasq/docs/dnsmasq-man.html
                # "Note that once set, the DUID is stored in the lease database..."
                if len(elements) < 5:
                    continue

                try:
                    # elements[0] is the expiration time (seconds since unix epoch),
                    #   0 means infinite (static lease)
                    # elements[1] is the MAC address for IPv4 entries and the IAID for IPv6 entries
                    # elements[2] is the IP address
                    # elements[3] is the hostname or "*" if none
                    # elements[4] is the client identifier for IPv4 entries and the client DUID for
                    #   IPv6
                    if ":" in elements[1]:
                        result["ipv4"].append(
                            {
                                "expiry": int(elements[0]),
                                "macAddress": elements[1],
                                "ipAddress": elements[2],
                                "hostname": elements[3],
                                "clientIdentifer": elements[4],
                            }
                        )
                    else:
                        result["ipv6"].append(
                            {
                                "expiry": int(elements[0]),
                                "iaid": elements[1],
                                "ipAddress": elements[2],
                                "hostname": elements[3],
                                "clientDuid": elements[4],
                            }
                        )
                except Exception:
                    # Skip any entry we can't parse
                    pass
        return result

    @staticmethod
    async def get_supplicant_interfaces() -> list[str]:
        """
        Retrieve a list of object paths to interfaces known to the supplicant
        """
        bus = await DBusManager().get_bus()

        reply = await bus.call(
            Message(
                destination=definition.WPA_IFACE,
                path=definition.WPA_OBJ,
                interface=definition.DBUS_PROP_IFACE,
                member="Get",
                signature="ss",
                body=[definition.WPA_IFACE, "Interfaces"],
            )
        )

        if reply.message_type == MessageType.ERROR:
            raise Exception("Unable to retrieve supplicant interfaces")

        return variant_to_python(reply.body[0])

    @staticmethod
    async def get_supplicant_interface_name(interface_obj_path: str) -> str:
        """
        Retrieve the name of an interface known to the supplicant by its object path
        """
        bus = await DBusManager().get_bus()

        reply = await bus.call(
            Message(
                destination=definition.WPA_IFACE,
                path=interface_obj_path,
                interface=definition.DBUS_PROP_IFACE,
                member="Get",
                signature="ss",
                body=[SUPPLICANT_INTERFACE_IFACE, "Ifname"],
            )
        )

        if reply.message_type == MessageType.ERROR:
            raise Exception("Unable to retrieve supplicant interface name")

        return variant_to_python(reply.body[0])

    @staticmethod
    async def get_summit_status(ifname: Optional[str] = "wlan0") -> dict[str, str]:
        """
        Retrieve the Summit status info for the specified interface from the supplicant (default is
        wlan0)
        """
        interface_obj_paths = await NetworkService().get_supplicant_interfaces()

        for interface_obj_path in interface_obj_paths:
            interface_name = await NetworkService().get_supplicant_interface_name(
                interface_obj_path
            )
            if interface_name == ifname:
                bus = await DBusManager().get_bus()

                reply = await bus.call(
                    Message(
                        destination=definition.WPA_IFACE,
                        path=interface_obj_path,
                        interface=definition.DBUS_PROP_IFACE,
                        member="Get",
                        signature="ss",
                        body=[SUPPLICANT_INTERFACE_IFACE, "SummitStatus"],
                    )
                )

                if reply.message_type == MessageType.ERROR:
                    raise Exception("Unable to retrieve Summit status info")

                return variant_to_python(reply.body[0])

        # If not found, raise exception
        raise InterfaceNotFoundError("interface not found")


class ConnectionProfileReservedError(Exception):
    """Custom error class for when the requested connection profile is reserved."""


class ConnectionProfileNotFoundError(Exception):
    """Custom error class for when the requested connection profile was not found."""


class ConnectionProfileAlreadyActiveError(Exception):
    """
    Custom error class for when the user requests to activate a connection profile that is already
    active.
    """


class ConnectionProfileAlreadyInactiveError(Exception):
    """
    Custom error class for when the user requests to deactivate a connection profile that is already
    inactive.
    """


class WifiDeviceNotFoundError(Exception):
    """
    Custom error class for when the user requests a scan for access points, but no Wi-Fi device is
    found.
    """


class InterfaceNotFoundError(Exception):
    """
    Custom error class for when the user requests status information for a network interface that
    doesn't exist
    """
