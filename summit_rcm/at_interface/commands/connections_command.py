from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.settings import ServerConfig
from summit_rcm.services.network_manager_service import NetworkManagerService


class ConnectionsCommand(Command):
    NAME: str = "Connections"
    SIGNATURE: str = "at+lcon"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = ConnectionsCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {ConnectionsCommand.SIGNATURE}?\r\n",
            )
        try:
            connections_str = await get_connections()
            return (True, f"\r\n{connections_str}")
        except Exception as e:
            syslog(LOG_ERR, f"Error getting connection {str(e)}")
            return (True, "\r\nError\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in ConnectionsCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param == ""
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+LCON\r\n"

    @staticmethod
    def signature() -> str:
        return ConnectionsCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return ConnectionsCommand.NAME


async def get_connections() -> str:
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
    return_str = ""
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

        # Add the connection to the dictionary
        if connection_settings_connection.get("uuid", None) is not None:
            uuid = connection_settings_connection["uuid"].value
        else:
            continue
        return_str += f"{str(uuid)}:{entry['id']},{entry['activated']}\r\n"
    return return_str
