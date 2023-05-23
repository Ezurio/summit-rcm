"""
File that consists of the VirtualInterface Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.network_service import NetworkService


class VirtualInterfaceCommand(Command):
    """
    AT Command to add or remove a virtual interface
    """

    NAME: str = "Virtual Interface"
    SIGNATURE: str = "at+netifvirt"
    VALID_NUM_PARAMS: List[int] = [1]
    DEVICE_TYPE: str = ""

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = VirtualInterfaceCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {VirtualInterfaceCommand.SIGNATURE}?\r\n",
            )
        try:
            if params_dict["add"]:
                await NetworkService().add_virtual_interface()
            else:
                await NetworkService().remove_virtual_interface()
            return (True, "\r\nOK\r\n")
        except Exception as exception:
            syslog(
                LOG_ERR, f"Error adding/removing virtual interface: {str(exception)}"
            )
            return (True, "\r\nError\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in VirtualInterfaceCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        try:
            params_dict["add"] = int(params_list[0])
            if params_dict["add"] not in (0, 1):
                raise ValueError
        except ValueError:
            valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+NETIFVIRT=<add>\r\n"

    @staticmethod
    def signature() -> str:
        return VirtualInterfaceCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return VirtualInterfaceCommand.NAME
