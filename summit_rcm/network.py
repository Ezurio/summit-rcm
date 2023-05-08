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
            unmanaged_devices = (
                ServerConfig()
                .get_parser()
                .get("summit-rcm", "unmanaged_hardware_devices", fallback="")
                .split()
            )

            # Get a list of all known connections (profiles)
            try:
                settings_props = await NetworkManagerService().get_obj_properties(
                    NetworkManagerService().NM_SETTINGS_OBJ_PATH,
                    NetworkManagerService().NM_SETTINGS_IFACE,
                )
            except Exception as e:
                syslog(LOG_ERR, f"Unable to read NetworkManager settings - {str(e)}")
                result["InfoMsg"] = "Unable to read NetworkManager settings"
                result["SDCERR"] = definition.SUMMIT_RCM_ERRORS.get("SDCERR_FAIL")
                resp.media = result
                return

            connection_obj_paths = settings_props.get("Connections", [])

            try:
                manager_props = await NetworkManagerService().get_obj_properties(
                    NetworkManagerService().NM_CONNECTION_MANAGER_OBJ_PATH,
                    NetworkManagerService().NM_CONNECTION_MANAGER_IFACE,
                )
            except Exception as e:
                syslog(LOG_ERR, f"Unable to read NetworkManager properties - {str(e)}")
                result["InfoMsg"] = "Unable to read NetworkManager properties"
                result["SDCERR"] = definition.SUMMIT_RCM_ERRORS.get("SDCERR_FAIL")
                resp.media = result
                return
            active_connection_obj_paths = manager_props.get("ActiveConnections", [])

            # Loop through the connections and build a dictionary to return
            for conn in connection_obj_paths:
                try:
                    connection_settings = (
                        await NetworkManagerService().get_connection_settings(conn)
                    )
                except Exception as e:
                    syslog(
                        LOG_ERR,
                        f"Unable to read connection settings for {str(conn)} - {str(e)}",
                    )
                    continue

                connection_settings_connection = connection_settings.get(
                    "connection", None
                )
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
                entry["activated"] = 0
                for active_connection in active_connection_obj_paths:
                    try:
                        active_connection_props = (
                            await NetworkManagerService().get_obj_properties(
                                active_connection,
                                NetworkManagerService().NM_CONNECTION_ACTIVE_IFACE,
                            )
                        )
                    except Exception as e:
                        syslog(
                            LOG_ERR,
                            f"Unable to read properties of active connection - {str(e)}",
                        )
                        continue
                    active_connection_connection_obj_path = (
                        active_connection_props["Connection"]
                        if active_connection_props.get("Connection", None) is not None
                        else ""
                    )
                    if active_connection_connection_obj_path == conn:
                        entry["activated"] = 1
                        break
                entry["id"] = (
                    connection_settings_connection["id"].value
                    if connection_settings_connection.get("id", None) is not None
                    else ""
                )

                # Check if the connection is an AP
                entry["type"] = "n/a"
                try:
                    connenction_settings_wireless = connection_settings.get(
                        "802-11-wireless", None
                    )
                    if connenction_settings_wireless is not None:
                        entry["type"] = (
                            connenction_settings_wireless["mode"].value
                            if connenction_settings_wireless.get("mode", None)
                            is not None
                            else "infrastructure"
                        )
                except Exception as e:
                    # Couldn't read the wireless settings, so assume it's not an AP
                    syslog(
                        LOG_ERR,
                        f"Unable to read connection settings wireless for {str(conn)} - {str(e)}",
                    )
                    pass

                # Add the connection to the dictionary
                uuid = (
                    connection_settings_connection["uuid"].value
                    if connection_settings_connection.get("uuid", None) is not None
                    else ""
                )
                result["connections"][uuid] = entry
            result["count"] = len(result["connections"])

            resp.media = result
        except Exception as e:
            syslog(LOG_ERR, f"Error retrieving connections - {str(e)}")
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

            try:
                connection_obj_path = (
                    await NetworkManagerService().get_connection_obj_path_by_uuid(uuid)
                )
                if connection_obj_path is None or connection_obj_path == "":
                    raise Exception("UUID not found")
            except Exception as e:
                result["InfoMsg"] = str(e)
                resp.media = result
                return

            if media.get("activate") == 1 or media.get("activate") == "1":
                try:
                    connection_props = (
                        await NetworkManagerService().get_connection_settings(
                            connection_obj_path
                        )
                    )
                    connection_setting_connection = connection_props.get(
                        "connection", {}
                    )
                    if connection_setting_connection.get("type", None) is None:
                        raise Exception("Unable to read connection settings")

                    if connection_setting_connection["type"].value == "bridge":
                        await NetworkManagerService().activate_connection(
                            connection_obj_path, "/", "/"
                        )
                        result["SDCERR"] = 0
                        result["InfoMsg"] = "Bridge activated"
                        resp.media = result
                        return
                    else:
                        interface_name = (
                            connection_setting_connection["interface-name"].value
                            if connection_setting_connection.get("interface-name", None)
                            is not None
                            else ""
                        )
                        if interface_name == "":
                            raise Exception(
                                "Could not find valid interface for the connection profile"
                            )

                        all_devices = await NetworkManagerService().get_all_devices()
                        for dev_obj_path in all_devices:
                            dev_props = (
                                await NetworkManagerService().get_obj_properties(
                                    dev_obj_path,
                                    NetworkManagerService().NM_DEVICE_IFACE,
                                )
                            )

                            dev_interface_name = dev_props.get("Interface", None)
                            if dev_interface_name is None:
                                continue

                            if dev_interface_name == interface_name:
                                await NetworkManagerService().activate_connection(
                                    connection_obj_path, dev_obj_path, "/"
                                )
                                result["SDCERR"] = 0
                                result["InfoMsg"] = "Connection Activated"
                                resp.media = result
                                return

                        raise Exception("appropriate device not found")
                except Exception as e:
                    result["InfoMsg"] = f"Unable to activate connection - {str(e)}"
                    resp.media = result
                    return
            else:
                try:
                    manager_props = await NetworkManagerService().get_obj_properties(
                        NetworkManagerService().NM_CONNECTION_MANAGER_OBJ_PATH,
                        NetworkManagerService().NM_CONNECTION_MANAGER_IFACE,
                    )
                    active_connection_obj_paths = manager_props.get(
                        "ActiveConnections", []
                    )

                    for active_connection_obj_path in active_connection_obj_paths:
                        active_connection_props = (
                            await NetworkManagerService().get_obj_properties(
                                active_connection_obj_path,
                                NetworkManagerService().NM_CONNECTION_ACTIVE_IFACE,
                            )
                        )

                        active_connection_uuid = active_connection_props.get(
                            "Uuid", None
                        )
                        if active_connection_uuid is None:
                            continue

                        if uuid == active_connection_uuid:
                            await NetworkManagerService().deactivate_connection(
                                active_connection_obj_path
                            )
                            result["SDCERR"] = 0
                            result["InfoMsg"] = "Connection Deactivated"
                            resp.media = result
                            return

                    result["SDCERR"] = 0
                    result["InfoMsg"] = "Already inactive. No action taken"
                except Exception as e:
                    result["InfoMsg"] = f"Unable to deactivate connection - {str(e)}"
                    resp.media = result
                    return
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

            try:
                settings_props = await NetworkManagerService().get_obj_properties(
                    NetworkManagerService().NM_SETTINGS_OBJ_PATH,
                    NetworkManagerService().NM_SETTINGS_IFACE,
                )
            except Exception as e:
                syslog(LOG_ERR, f"Unable to read NetworkManager settings - {str(e)}")
                result["InfoMsg"] = "Unable to read NetworkManager settings"
                resp.media = result
                return

            connection_obj_paths = settings_props.get("Connections", [])
            connections = []
            for connection_obj_path in connection_obj_paths:
                connection_props = (
                    await NetworkManagerService().get_connection_settings(
                        connection_obj_path
                    )
                )

                connection_settings_connection = connection_props.get("connection", {})
                connection_id = (
                    connection_settings_connection["id"].value
                    if connection_settings_connection.get("id", None) is not None
                    else ""
                )
                connection_uuid = (
                    connection_settings_connection["uuid"].value
                    if connection_settings_connection.get("uuid", None) is not None
                    else ""
                )
                if connection_id == "" or connection_uuid == "":
                    continue

                connections.append(
                    {
                        "obj_path": connection_obj_path,
                        "id": connection_id,
                        "uuid": connection_uuid,
                    }
                )

            existing_connection = None
            for connection in connections:
                if (
                    post_data["connection"].get("uuid", None) is not None
                    and connection["uuid"] == post_data["connection"]["uuid"]
                ):
                    existing_connection = connection
                if id == connection["id"]:
                    con_uuid = connection["uuid"]
                    if t_uuid and con_uuid and (con_uuid != t_uuid):
                        raise Exception("Provided uuid does not match uuid of given id")
                    t_uuid = con_uuid

                    break

            if post_data.get("connection") and not post_data["connection"].get("uuid"):
                post_data["connection"]["uuid"] = t_uuid

            if post_data["connection"]["uuid"] == "":
                del post_data["connection"]["uuid"]

            name = post_data["connection"].get("id", "")
            if existing_connection:
                # Connection already exists, delete it
                exisiting_connection_props = (
                    await NetworkManagerService().get_connection_settings(
                        existing_connection["obj_path"]
                    )
                )

                try:
                    await NetworkManagerService().delete_connection(
                        existing_connection["obj_path"]
                    )
                except Exception as delete_existing_exception:
                    # Could not remove the existing connection
                    syslog(
                        LOG_ERR,
                        f"Could not update connection {name} - {str(delete_existing_exception)}",
                    )
                    result["InfoMsg"] = f"Could not update connection {name}"
                    resp.media = result
                    return

                try:
                    await NetworkManagerService().add_connection(
                        await NetworkManagerService().prepare_new_connection_data(
                            post_data
                        )
                    )
                    result["InfoMsg"] = f"connection {name} updated"
                    result["SDCERR"] = 0
                    resp.media = result
                    return
                except Exception as add_connection_exception:
                    # Could not add new connnection, restore existing connection
                    syslog(
                        LOG_ERR,
                        f"An error occurred trying to save config, restoring original - {str(add_connection_exception)}",
                    )
                    try:
                        await NetworkManagerService().add_connection(
                            exisiting_connection_props
                        )
                        result[
                            "InfoMsg"
                        ] = "An error occurred trying to save config: Original config restored"
                        resp.media = result
                        return
                    except Exception as restore_original_exception:
                        # Could not restore existing connection
                        syslog(
                            LOG_ERR,
                            f"Unable to restore origin config - {str(restore_original_exception)}",
                        )
                        result[
                            "InfoMsg"
                        ] = "An error occurred trying to save config: Unable to restore original config"
                        resp.media = result
                        return
            else:
                # Connection does not already exist, so create a new one
                try:
                    await NetworkManagerService().add_connection(
                        await NetworkManagerService().prepare_new_connection_data(
                            post_data
                        )
                    )
                except Exception as add_connection_exception:
                    result["SDCERR"] = 1
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
            resp.media = result

    async def on_delete(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 1, "InfoMsg": ""}
        uuid = req.params.get("uuid", "")
        try:
            connection_obj_path = (
                await NetworkManagerService().get_connection_obj_path_by_uuid(uuid)
            )
            if connection_obj_path is None or connection_obj_path == "":
                raise Exception("not found")

            await NetworkManagerService().delete_connection(connection_obj_path)
            result["InfoMsg"] = "Connection deleted"
            result["SDCERR"] = 0
        except Exception as e:
            result["InfoMsg"] = f"Unable to delete connection - {str(e)}"

        resp.media = result

    async def on_get(self, req, resp):
        def cert_to_filename(cert):
            """
            Return base name only.
            """
            if cert:
                return cert[len(definition.FILEDIR_DICT["cert"]) :]

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

            if extended:
                try:
                    (
                        ret,
                        msg,
                        settings,
                    ) = await NetworkService().get_extended_connection_settings(uuid)

                    if ret < 0:
                        result["InfoMsg"] = msg
                    else:
                        result["connection"] = settings
                        result["SDCERR"] = ret
                except Exception as e_extended:
                    syslog(
                        LOG_ERR,
                        f"Unable to retrieve extended connection settings: {str(e_extended)}",
                    )
                    result[
                        "InfoMsg"
                    ] = "Unable to retrieve extended connecting settings"

                resp.media = result
                return
            else:
                # Get a list of all known connections (profiles)
                try:
                    settings_props = await NetworkManagerService().get_obj_properties(
                        NetworkManagerService().NM_SETTINGS_OBJ_PATH,
                        NetworkManagerService().NM_SETTINGS_IFACE,
                    )
                except Exception as e:
                    syslog(
                        LOG_ERR, f"Unable to read NetworkManager settings - {str(e)}"
                    )
                    result["InfoMsg"] = "Unable to read NetworkManager settings"
                    result["SDCERR"] = definition.SUMMIT_RCM_ERRORS.get("SDCERR_FAIL")
                    resp.media = result
                    return

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
                                    settings[setting][property] = cert_to_filename(
                                        settings[setting][property].value
                                    )
                                    continue

                                # Handle ip config special cases
                                if setting in ["ipv4", "ipv6"]:
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
                                                if route.get("next-hop", None)
                                                is not None
                                                else None
                                            )
                                            route["metric"] = (
                                                route["metric"].value
                                                if route.get("metric", None) is not None
                                                else -1
                                            )
                                        settings[setting][property] = route_data
                                        continue

                                    # Handle addresses and routes special cases (these properties
                                    # are deprecated)
                                    if property in ["addresses", "routes"]:
                                        properties_to_delete.append(property)
                                        continue

                                settings[setting][property] = settings[setting][
                                    property
                                ].value

                            # Remove properties marked for deletion (deprecated properties)
                            for property in properties_to_delete:
                                del settings[setting][property]

                        result["connection"] = settings
                        result["SDCERR"] = 0
                        resp.media = result
                        return

                result["InfoMsg"] = "Invalid UUID"
        except Exception as e:
            syslog(LOG_ERR, f"Invalid UUID: {str(e)}")
            result["InfoMsg"] = "Invalid UUID"

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
