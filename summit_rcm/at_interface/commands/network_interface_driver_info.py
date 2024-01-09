"""
File that consists of the NetworkInterfaceDriverInfo Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.network_service import NetworkService


class NetworkInterfaceDriverInfoCommand(Command):
    """
    AT Command to retrieve driver info on a specific network interface
    """

    NAME: str = "Network Interface Driver Info"
    SIGNATURE: str = "at+netifdrvinf"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = NetworkInterfaceDriverInfoCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            driver_info = await NetworkService.get_interface_driver_info(
                params_dict["interface name"]
            )

            return (
                True,
                f"+NETIFDRVINF: {driver_info['adoptedCountryCode']},"
                f"{driver_info['otpCountryCode']}\r\nOK",
            )
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Error getting network interface driver info: {str(exception)}",
            )
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in NetworkInterfaceDriverInfoCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if not valid:
            return (False, {})
        params_dict["interface name"] = params_list[0]
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+NETIFDRVINF=<interface name>"

    @staticmethod
    def signature() -> str:
        return NetworkInterfaceDriverInfoCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return NetworkInterfaceDriverInfoCommand.NAME
