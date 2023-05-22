from syslog import syslog, LOG_ERR
import falcon
from summit_rcm.services.network_manager_service import (
    NM80211ApFlags,
    NM80211ApSecurityFlags,
    NMDeviceType,
    NetworkManagerService,
)
from summit_rcm.services.network_service import NetworkService
from summit_rcm import definition
from summit_rcm.settings import ServerConfig


class NetworkConnections:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 0, "InfoMsg": "", "count": 0, "connections": {}}

        try:
            result["connections"] = await NetworkService.get_all_connection_profiles(
                is_legacy=True
            )
            result["count"] = len(result["connections"])

            resp.media = result
        except Exception as exception:
            syslog(LOG_ERR, f"Error retrieving connections - {str(exception)}")
            result["InfoMsg"] = "Error retrieving connections"
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS.get("SDCERR_FAIL")
            resp.media = result


class NetworkConnection:
    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 1, "InfoMsg": "unable to set connection"}
        try:
            media = await req.get_media()
            uuid = media.get("uuid", None)
            if not uuid:
                result["InfoMsg"] = "Missing UUID"
                resp.media = result
                return

            if media.get("activate") == 1 or media.get("activate") == "1":
                try:
                    await NetworkService.activate_connection_profile(uuid=uuid)
                    result["SDCERR"] = 0
                    result["InfoMsg"] = "Connection Activated"
                except Exception as e:
                    result["SDCERR"] = 1
                    result["InfoMsg"] = f"Unable to activate connection - {str(e)}"
                resp.media = result
                return

            try:
                await NetworkService.deactivate_connection_profile(uuid=uuid)
                result["SDCERR"] = 0
                result["InfoMsg"] = "Connection Deactivated"
            except Exception as e:
                result["InfoMsg"] = f"Unable to deactivate connection - {str(e)}"
        except Exception as e:
            syslog(LOG_ERR, f"exception during NetworkConnection PUT: {e}")
            result["InfoMsg"] = f"Internal error - exception from NetworkManager: {e}"
        resp.media = result

    async def on_post(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 1, "InfoMsg": ""}

        try:
            post_data = await req.get_media()
            if not post_data.get("connection"):
                result["InfoMsg"] = "Missing connection section"
                resp.media = result
                return

            t_uuid = post_data["connection"].get("uuid", None)
            id = post_data["connection"].get("id", None)

            if not id:
                result["InfoMsg"] = "connection section must have an id element"
                resp.media = result
                return

            existing_connection = False
            try:
                for uuid, info in (
                    await NetworkService.get_all_connection_profiles(is_legacy=True)
                ).items():
                    if t_uuid and t_uuid == uuid:
                        existing_connection = True
                    if id == info.get("id"):
                        if t_uuid and (uuid != t_uuid):
                            raise Exception(
                                "Provided uuid does not match uuid of given id"
                            )
                        t_uuid = uuid
            except Exception as exception:
                result["InfoMsg"] = f"Could not update connection - {str(exception)}"
                resp.media = result
                return

            if post_data.get("connection") and not post_data["connection"].get("uuid"):
                post_data["connection"]["uuid"] = t_uuid

            if post_data["connection"]["uuid"] == "":
                del post_data["connection"]["uuid"]

            name = post_data["connection"].get("id", "")
            if existing_connection:
                try:
                    # Connection already exists, update it
                    await NetworkService.update_connection_profile(
                        new_settings=post_data, uuid=t_uuid, id=None, is_legacy=True
                    )
                    result["InfoMsg"] = f"connection {name} updated"
                    result["SDCERR"] = 0
                    resp.media = result
                    return
                except Exception as update_connection_exception:
                    syslog(
                        LOG_ERR,
                        f"Could not update connection {name} - {str(update_connection_exception)}",
                    )
                    result["InfoMsg"] = f"Could not update connection {name}"
                    resp.media = result
                    return
            else:
                # Connection does not already exist, so create a new one
                try:
                    await NetworkService.create_connection_profile(
                        settings=post_data, overwrite_existing=False, is_legacy=True
                    )
                except Exception as add_connection_exception:
                    result["SDCERR"] = 1
                    syslog(
                        LOG_ERR,
                        f"Unable to create connection - {str(add_connection_exception)}",
                    )
                    result[
                        "InfoMsg"
                    ] = f"Unable to create connection - {str(add_connection_exception)}"
                    resp.media = result
                    return
                result["InfoMsg"] = f"connection {name} created"
                result["SDCERR"] = 0
                resp.media = result
        except Exception as e:
            result["SDCERR"] = 1
            result["InfoMsg"] = f"Unable to create connection - {str(e)}"
            syslog(LOG_ERR, f"Unable to create connection - {str(e)}")
            resp.media = result

    async def on_delete(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 1, "InfoMsg": ""}
        uuid = req.params.get("uuid", "")
        try:
            await NetworkService.delete_connection_profile(uuid=uuid, id=None)
            result["InfoMsg"] = "Connection deleted"
            result["SDCERR"] = 0
        except Exception as e:
            result["InfoMsg"] = f"Unable to delete connection - {str(e)}"

        resp.media = result

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 1, "InfoMsg": ""}
        try:
            uuid = req.params.get("uuid", None)
            if not uuid:
                result["InfoMsg"] = "no UUID provided"
                resp.media = result
                return

            extended_test = -1
            try:
                extended = req.params.get("extended", None)
                if extended is not None:
                    extended = extended.lower()
                    if extended in ("y", "yes", "t", "true", "on", "1"):
                        extended_test = 1
                        extended = True
                    elif extended in ("n", "no", "f", "false", "off", "0"):
                        extended_test = 0
                        extended = False
                    if extended_test < 0:
                        raise ValueError("illegal value passed in")
                else:
                    # Default to 'non-extended' mode when 'extended' parameter is omitted
                    extended = False
            except Exception:
                result["SDCERR"] = definition.SUMMIT_RCM_ERRORS.get("SDCERR_FAIL")
                result["InfoMsg"] = (
                    "Unable to get extended connection info. Supplied extended parameter '%s' invalid."
                    % req.params.get("extended")
                )
                resp.media = result
                return

            result["connection"] = await NetworkService.get_connection_profile_settings(
                uuid=uuid, id=None, extended=extended, is_legacy=True
            )
            result["SDCERR"] = 0
        except Exception as exception:
            result["InfoMsg"] = f"Unable to retrieve connection info - {str(exception)}"
            result["SDCERR"] = 1
        resp.media = result


class NetworkAccessPoints:
    async def on_put(self, req, resp):
        """
        Start a manual scan
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 1, "InfoMsg": ""}

        try:
            dev_obj_paths = await NetworkManagerService().get_all_devices()
            for dev_obj_path in dev_obj_paths:
                dev_properties = await NetworkManagerService().get_obj_properties(
                    dev_obj_path, NetworkManagerService().NM_DEVICE_IFACE
                )
                if (
                    dev_properties.get(
                        "DeviceType", NMDeviceType.NM_DEVICE_TYPE_UNKNOWN
                    )
                    == NMDeviceType.NM_DEVICE_TYPE_WIFI
                ):
                    await NetworkManagerService().wifi_device_request_scan(
                        dev_obj_path, {}
                    )
                    result["SDCERR"] = 0
                    result["InfoMsg"] = "Scan requested"
                    break
        except Exception as e:
            result["InfoMsg"] = f"Unable to start scan request: {str(e)}"

        resp.media = result

    async def on_get(self, req, resp):
        """Get Cached AP list"""

        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": 1,
            "InfoMsg": "",
            "count": 0,
            "accesspoints": [],
        }

        try:
            dev_obj_paths = await NetworkManagerService().get_all_devices()
            for dev_obj_path in dev_obj_paths:
                dev_properties = await NetworkManagerService().get_obj_properties(
                    dev_obj_path, NetworkManagerService().NM_DEVICE_IFACE
                )
                if (
                    dev_properties.get(
                        "DeviceType", NMDeviceType.NM_DEVICE_TYPE_UNKNOWN
                    )
                    == NMDeviceType.NM_DEVICE_TYPE_WIFI
                ):
                    wireless_properties = (
                        await NetworkManagerService().get_obj_properties(
                            dev_obj_path,
                            NetworkManagerService().NM_DEVICE_WIRELESS_IFACE,
                        )
                    )
                    for ap_obj_path in wireless_properties.get("AccessPoints", []):
                        ap = await NetworkManagerService().get_obj_properties(
                            ap_obj_path,
                            NetworkManagerService().NM_ACCESS_POINT_IFACE,
                        )
                        security_string = ""
                        keymgmt = "none"
                        flags = ap.get("Flags", NM80211ApFlags.NM_802_11_AP_FLAGS_NONE)
                        wpa_flags = ap.get(
                            "WpaFlags", NM80211ApSecurityFlags.NM_802_11_AP_SEC_NONE
                        )
                        rsn_flags = ap.get(
                            "RsnFlags", NM80211ApSecurityFlags.NM_802_11_AP_SEC_NONE
                        )
                        if (
                            flags & NM80211ApFlags.NM_802_11_AP_FLAGS_PRIVACY
                            and wpa_flags
                            == NM80211ApSecurityFlags.NM_802_11_AP_SEC_NONE
                            and rsn_flags
                            == NM80211ApSecurityFlags.NM_802_11_AP_SEC_NONE
                        ):
                            security_string = security_string + "WEP "
                            keymgmt = "static"

                        if wpa_flags != NM80211ApSecurityFlags.NM_802_11_AP_SEC_NONE:
                            security_string = security_string + "WPA1 "

                        if rsn_flags != NM80211ApSecurityFlags.NM_802_11_AP_SEC_NONE:
                            security_string = security_string + "WPA2 "

                        if (
                            wpa_flags
                            & NM80211ApSecurityFlags.NM_802_11_AP_SEC_KEY_MGMT_802_1X
                            or rsn_flags
                            & NM80211ApSecurityFlags.M_802_11_AP_SEC_KEY_MGMT_802_1X
                        ):
                            security_string = security_string + "802.1X "
                            keymgmt = "wpa-eap"

                        if (
                            wpa_flags
                            & NM80211ApSecurityFlags.NM_802_11_AP_SEC_KEY_MGMT_PSK
                        ) or (
                            rsn_flags
                            & NM80211ApSecurityFlags.NM_802_11_AP_SEC_KEY_MGMT_PSK
                        ):
                            security_string = security_string + "PSK"
                            keymgmt = "wpa-psk"

                        ssid = ap.get("Ssid", None)
                        ap_data = {
                            "SSID": ssid.decode("utf-8") if ssid is not None else "",
                            "HwAddress": ap.get("HwAddress", ""),
                            "Strength": ap.get("Strength", 0),
                            "MaxBitrate": ap.get("MaxBitrate", 0),
                            "Frequency": ap.get("Frequency", 0),
                            "Flags": flags,
                            "WpaFlags": wpa_flags,
                            "RsnFlags": rsn_flags,
                            "LastSeen": ap.get("LastSeen", -1),
                            "Security": security_string,
                            "Keymgmt": keymgmt,
                        }
                        result["accesspoints"].append(ap_data)

                    if len(result["accesspoints"]) > 0:
                        result["SDCERR"] = 0
                        result["count"] = len(result["accesspoints"])
                    else:
                        result["InfoMsg"] = "No access points found"

        except Exception as e:
            result["InfoMsg"] = "Unable to get access point list"
            syslog(f"NetworkAccessPoints GET exception: {e}")

        resp.media = result


class NetworkInterfaces:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 1, "InfoMsg": "", "interfaces": []}

        try:
            result["SDCERR"] = 0
            result["interfaces"] = await NetworkService.get_all_interfaces()
        except Exception as e:
            result["InfoMsg"] = "Could not retrieve list of interfaces"
            syslog(f"NetworkInterfaces GET exception: {e}")

        resp.media = result

    async def on_post(self, req, resp):
        """
        Add virtual interface
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 1, "InfoMsg": ""}

        post_data = await req.get_media()
        if not post_data.get("interface"):
            result["InfoMsg"] = "Missing interface section"
            resp.media = result
            return
        interface = post_data.get("interface")
        if not post_data.get("type"):
            result["InfoMsg"] = "Missing type section"
            resp.media = result
            return
        int_type = post_data.get("type")
        if int_type == "STA":
            int_type = "managed"

        if interface != "wlan1":
            result[
                "InfoMsg"
            ] = f"Invalid interface {interface}. Supported interface wlan1"
            resp.media = result
            return

        if int_type != "managed":
            result["InfoMsg"] = f"Invalid type {int_type}. Supported type: STA"
            resp.media = result
            return

        # Currently only support wlan1/managed
        result["InfoMsg"] = f"Unable to add virtual interface {interface}."

        if await NetworkService.add_virtual_interface():
            result["SDCERR"] = 0
            result["InfoMsg"] = f"Virtual interface {interface} added"

        resp.media = result

    async def on_delete(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        interface = str(req.params.get("interface", ""))
        result = {"SDCERR": 1, "InfoMsg": f"Unable to remove interface {interface}"}

        if interface != "wlan1":
            resp.media = result
            return

        if await NetworkService.remove_virtual_interface():
            result["SDCERR"] = 0
            result["InfoMsg"] = f"Virtual interface {interface} removed"

        resp.media = result


class NetworkInterface:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 1, "InfoMsg": ""}
        try:
            name = req.params.get("name", None)
            if not name:
                result["InfoMsg"] = "no interface name provided"
                resp.media = result
                return

            unmanaged_devices = (
                ServerConfig()
                .get_parser()
                .get("summit-rcm", "unmanaged_hardware_devices", fallback="")
                .split()
            )
            if name in unmanaged_devices:
                result["InfoMsg"] = "invalid interface name provided"
                resp.media = result
                return

            result["properties"] = await NetworkService.get_interface_status(
                target_interface_name=name, is_legacy=True
            )
            if len(result["properties"]) == 0:
                result["InfoMsg"] = "invalid interface name provided"
                resp.media = result
                return

            result["SDCERR"] = 0
        except Exception as e:
            syslog(
                LOG_ERR,
                f"Unable to retrieve detailed network interface configuration: {str(e)}",
            )
            result[
                "InfoMsg"
            ] = "Unable to retrieve detailed network interface configuration"
            result["SDCERR"] = 1

        resp.media = result


class NetworkInterfaceStatistics(object):
    async def on_get(self, req, resp):
        """
        Retrieve receive/transmit statistics for the requested interface
        """

        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": 1,
            "InfoMsg": "",
            "statistics": {
                "rx_bytes": -1,
                "rx_packets": -1,
                "rx_errors": -1,
                "rx_dropped": -1,
                "multicast": -1,
                "tx_bytes": -1,
                "tx_packets": -1,
                "tx_errors": -1,
                "tx_dropped": -1,
            },
        }

        try:
            name = req.params.get("name", None)
            if not name:
                result["InfoMsg"] = "No interface name provided"
                return result

            (success, stats) = await NetworkService.get_interface_statistics(
                target_interface_name=name, is_legacy=True
            )
            if success:
                result["SDCERR"] = 0
                result["statistics"] = stats
        except Exception as e:
            result["InfoMsg"] = f"Could not read interface statistics - {str(e)}"
        resp.media = result


class WifiEnable:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": definition.SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")}

        try:
            connection_manager_props = await NetworkManagerService().get_obj_properties(
                NetworkManagerService().NM_CONNECTION_MANAGER_OBJ_PATH,
                NetworkManagerService().NM_CONNECTION_MANAGER_IFACE,
            )
            result["wifi_radio_software_enabled"] = connection_manager_props.get(
                "WirelessEnabled", False
            )
            result["wifi_radio_hardware_enabled"] = connection_manager_props.get(
                "WirelessHardwareEnabled", False
            )
            result["InfoMsg"] = "wifi enable results"
        except Exception as e:
            syslog(f"Unable to read WirelessEnabled status - {str(e)}")
            result["InfoMsg"] = "Unable to read WirelessEnabled status"
            result["wifi_radio_software_enabled"] = False
            result["wifi_radio_hardware_enabled"] = False
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"]

        resp.media = result

    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {}

        # Parse the inputs
        enable_test = -1
        try:
            enable = req.params.get("enable")
            enable = enable.lower()
            if enable in ("y", "yes", "t", "true", "on", "1"):
                enable_test = 1
            elif enable in ("n", "no", "f", "false", "off", "0"):
                enable_test = 0
            if enable_test < 0:
                raise ValueError("illegal value passed in")
        except Exception:
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS.get("SDCERR_FAIL")
            result["wifi_radio_software_enabled"] = False
            result["InfoMsg"] = (
                "unable to set WirelessEnabled. Supplied enable parameter '%s' invalid."
                % req.params.get("enable")
            )

            resp.media = result
            return

        # Set the value
        try:
            await NetworkManagerService().set_obj_properties(
                NetworkManagerService().NM_CONNECTION_MANAGER_OBJ_PATH,
                NetworkManagerService().NM_CONNECTION_MANAGER_IFACE,
                "WirelessEnabled",
                enable_test == 1,
                "b",
            )
        except Exception as e:
            syslog(f"Unable to set WirelessEnabled property - {str(e)}")
            result["InfoMsg"] = "Unable to set WirelessEnabled property"
            result["wifi_radio_software_enabled"] = False
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS.get("SDCERR_FAIL")
            resp.media = result
            return

        result["SDCERR"] = definition.SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
        result["InfoMsg"] = "wireless_radio_software_enabled: %s" % (
            "true" if enable_test == 1 else "false"
        )

        # Read the new value
        try:
            connection_manager_props = await NetworkManagerService().get_obj_properties(
                NetworkManagerService().NM_CONNECTION_MANAGER_OBJ_PATH,
                NetworkManagerService().NM_CONNECTION_MANAGER_IFACE,
            )
        except Exception as e:
            syslog(f"Unable to read WirelessEnabled status - {str(e)}")
            result["InfoMsg"] = "Unable to read WirelessEnabled status"
            result["wifi_radio_software_enabled"] = False
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
            resp.media = result
            return
        result["wifi_radio_software_enabled"] = connection_manager_props.get(
            "WirelessEnabled", False
        )
        resp.media = result