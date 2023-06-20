"""
File that consists of the WiFiEnabled Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.network_service import NetworkService


class WiFiEnabledCommand(Command):
    """
    AT Command to enable/disable wireless property in NetworkManager
    """

    NAME: str = "Enable/Disable Wi-Fi"
    SIGNATURE: str = "at+wenable"
    VALID_NUM_PARAMS: List[int] = [1]
    DEVICE_TYPE: str = ""

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = WiFiEnabledCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {WiFiEnabledCommand.SIGNATURE}?\r\n",
            )
        try:
            if params_dict["enabled"] != "":
                await NetworkService().set_wireless_enabled(params_dict["enabled"])
                return (True, "\r\nOK\r\n")
            wifi_enabled = await NetworkService().get_wireless_enabled()
            return (True, f"\r\n+WENABLE: {1 if wifi_enabled else 0}\r\nOK\r\n")
        except Exception as exception:
            syslog(
                LOG_ERR, f"Error enabling/disabling Wi-Fi: {str(exception)}"
            )
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in WiFiEnabledCommand.VALID_NUM_PARAMS
        try:
            params_dict["enabled"] = bool(int(params_list[0])) if params_list[0] else ""
        except ValueError:
            valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+WENABLE[=<enabled>]\r\n"

    @staticmethod
    def signature() -> str:
        return WiFiEnabledCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return WiFiEnabledCommand.NAME
