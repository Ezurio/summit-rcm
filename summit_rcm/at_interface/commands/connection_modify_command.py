"""
File that consists of the ConnectionModify Command Functionality
"""
from typing import List, Tuple
from syslog import syslog, LOG_ERR
from json import loads
from enum import IntEnum
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.network_service import (
    NetworkService,
    ConnectionProfileNotFoundError,
)


class Modes(IntEnum):
    CREATE = 0
    UDPATE = 1
    DELETE = 2


class ConnectionModifyCommand(Command):
    """
    AT Command to Create/Update/Delete a network connection profile
    """

    NAME: str = "Create/Update/Delete Connection"
    SIGNATURE: str = "at+connmod"
    VALID_NUM_PARAMS: List[int] = [2]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = ConnectionModifyCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            mode = params_dict["mode"]
            if params_dict["uuid"]:
                try:
                    uuid = await NetworkService().get_connection_profile_uuid_from_id(
                        params_dict["uuid"]
                    )
                except ConnectionProfileNotFoundError:
                    uuid = params_dict["uuid"]
            if mode == Modes.CREATE:
                await NetworkService().create_connection_profile(
                    params_dict["settings"]
                )
            elif mode == Modes.UDPATE:
                await NetworkService().update_connection_profile(
                    params_dict["settings"], uuid=uuid
                )
            elif mode == Modes.DELETE:
                await NetworkService().delete_connection_profile(uuid=uuid)
            return (True, "OK")
        except Exception as exception:
            syslog(LOG_ERR, f"Error Creating Connection: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",", 1)
        given_num_param = len(params_list)
        valid &= given_num_param in ConnectionModifyCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if not valid:
            return (False, {})
        try:
            params_dict["mode"] = int(params_list[0])
            mode = Modes(int(params_dict["mode"]))
            if mode == Modes.CREATE:
                params_dict["uuid"] = ""
                params_dict["settings"] = loads(params_list[1])
            elif mode == Modes.UDPATE:
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
        return "AT+CONNMOD=<mode>[,<uuid>|<id>][,<settings>]"

    @staticmethod
    def signature() -> str:
        return ConnectionModifyCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return ConnectionModifyCommand.NAME
