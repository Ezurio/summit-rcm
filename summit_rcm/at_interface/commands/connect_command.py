from typing import List, Tuple
from syslog import syslog, LOG_ERR
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.network_manager_service import NetworkManagerService


class ActivateConnectionCommand(Command):
    NAME: str = "Activate/Deactivate Connection"
    SIGNATURE: str = "at+acon"
    VALID_NUM_PARAMS: List[int] = [2]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = ActivateConnectionCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {ActivateConnectionCommand.SIGNATURE}?\r\n",
            )
        try:
            await activate_connection(params_dict["uuid"], params_dict["activate"])
            return (True, "\r\nOK\r\n")
        except Exception as e:
            syslog(LOG_ERR, f"Error Activating Connection {str(e)}")
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        given_num_param = len(params_list)
        valid &= given_num_param in ActivateConnectionCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if valid:
            params_dict["uuid"] = params_list[0]
            try:
                params_dict["activate"] = int(params_list[1])
            except Exception:
                valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+ACON=<uuid>,<activate>\r\n"

    @staticmethod
    def signature() -> str:
        return ActivateConnectionCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return ActivateConnectionCommand.NAME


async def activate_connection(uuid: str, activate: int):
    connection_obj_path = await NetworkManagerService().get_connection_obj_path_by_uuid(
        uuid
    )
    if connection_obj_path is None or connection_obj_path == "":
        raise Exception("UUID not found")

    if activate:
        connection_props = await NetworkManagerService().get_connection_settings(
            connection_obj_path
        )
        connection_setting_connection = connection_props.get("connection", {})
        if connection_setting_connection.get("type", None) is None:
            raise Exception("Unable to read connection settings")

        if connection_setting_connection["type"].value == "bridge":
            await NetworkManagerService().activate_connection(
                connection_obj_path, "/", "/"
            )
            return
        else:
            interface_name = (
                connection_setting_connection["interface-name"].value
                if connection_setting_connection.get("interface-name", None) is not None
                else ""
            )
            if interface_name == "":
                raise Exception(
                    "Could not find valid interface for the connection profile"
                )

            all_devices = await NetworkManagerService().get_all_devices()
            for dev_obj_path in all_devices:
                dev_props = await NetworkManagerService().get_obj_properties(
                    dev_obj_path,
                    NetworkManagerService().NM_DEVICE_IFACE,
                )

                dev_interface_name = dev_props.get("Interface", None)
                if dev_interface_name is None:
                    continue

                if dev_interface_name == interface_name:
                    await NetworkManagerService().activate_connection(
                        connection_obj_path, dev_obj_path, "/"
                    )
                    return

            raise Exception("appropriate device not found")

    else:
        manager_props = await NetworkManagerService().get_obj_properties(
            NetworkManagerService().NM_CONNECTION_MANAGER_OBJ_PATH,
            NetworkManagerService().NM_CONNECTION_MANAGER_IFACE,
        )
        active_connection_obj_paths = manager_props.get("ActiveConnections", [])

        for active_connection_obj_path in active_connection_obj_paths:
            active_connection_props = await NetworkManagerService().get_obj_properties(
                active_connection_obj_path,
                NetworkManagerService().NM_CONNECTION_ACTIVE_IFACE,
            )

            active_connection_uuid = active_connection_props.get("Uuid", None)
            if active_connection_uuid is None:
                continue

            if uuid == active_connection_uuid:
                await NetworkManagerService().deactivate_connection(
                    active_connection_obj_path
                )
                return
