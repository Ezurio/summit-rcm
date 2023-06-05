"""
File that consists of the ActivateConnection Command Functionality
"""
from typing import List, Tuple
from syslog import syslog, LOG_ERR
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.network_service import NetworkService
from summit_rcm.services.network_service import ConnectionProfileNotFoundError


class ActivateConnectionCommand(Command):
    """
    AT Command to activate or deactivate a connection profile
    """

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
            try:
                uuid = await NetworkService().get_connection_profile_uuid_from_id(
                    params_dict["uuid"]
                )
            except ConnectionProfileNotFoundError:
                uuid = params_dict["uuid"]
            if params_dict["activate"]:
                await NetworkService().activate_connection_profile(uuid=uuid)
            else:
                await NetworkService().deactivate_connection_profile(uuid=uuid)
            return (True, "\r\nOK\r\n")
        except Exception as exception:
            syslog(LOG_ERR, f"Error Activating Connection: {str(exception)}")
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
        return "\r\nAT+ACON=<uuid>|<id>,<activate>\r\n"

    @staticmethod
    def signature() -> str:
        return ActivateConnectionCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return ActivateConnectionCommand.NAME
