"""
File that consists of the ModifyConnection Command Functionality
"""
from typing import List, Tuple
from syslog import syslog, LOG_ERR
from json import loads
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.network_service import NetworkService, ConnectionProfileNotFoundError


class ModifyConnectionCommand(Command):
    """
    AT Command to Create/Update/Delete a network connection profile
    """

    NAME: str = "Create/Update/Delete Connection"
    SIGNATURE: str = "at+conn"
    VALID_NUM_PARAMS: List[int] = [2]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = ModifyConnectionCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {ModifyConnectionCommand.SIGNATURE}?\r\n",
            )
        try:
            mode = params_dict["mode"]
            if params_dict["uuid"]:
                try:
                    uuid = await NetworkService().get_connection_profile_uuid_from_id(
                        params_dict["uuid"]
                    )
                except ConnectionProfileNotFoundError:
                    uuid = params_dict["uuid"]
            if mode == 0:
                await NetworkService().create_connection_profile(
                    params_dict["settings"]
                )
            elif mode == 1:
                await NetworkService().update_connection_profile(params_dict["settings"], uuid=uuid)
            elif mode == 2:
                await NetworkService().delete_connection_profile(uuid=uuid)
            return (True, "\r\nOK\r\n")
        except Exception as exception:
            syslog(LOG_ERR, f"Error Creating Connection: {str(exception)}")
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",", 1)
        given_num_param = len(params_list)
        valid &= given_num_param in ModifyConnectionCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if valid:
            try:
                params_dict["mode"] = int(params_list[0])
                mode = params_dict["mode"]
                if mode not in (0, 1, 2):
                    raise ValueError
                if mode == 0:
                    params_dict["uuid"] = ""
                    params_dict["settings"] = loads(params_list[1])
                elif mode == 1:
                    params_list = params.split(",", 2)
                    params_dict["uuid"] = params_list[1]
                    params_dict["settings"] = loads(params_list[2])
                else:
                    params_dict["uuid"] = params_list[1]
                    params_dict["settings"] = ""
            except ValueError:
                valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+CONN=<mode>[,<uuid>|<id>][,<settings>]\r\n"

    @staticmethod
    def signature() -> str:
        return ModifyConnectionCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return ModifyConnectionCommand.NAME
