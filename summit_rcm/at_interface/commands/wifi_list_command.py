#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
File that consists of the WifiList Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.network_service import NetworkService


class WifiListCommand(Command):
    """
    AT Command to list cached Wifi AP's
    """

    NAME: str = "List Wifi Access Points"
    SIGNATURE: str = "at+wlist"
    VALID_NUM_PARAMS: List[int] = [1]
    DEVICE_TYPE: str = ""

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = WifiListCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            ap_str = ""
            ap_list = await NetworkService().get_access_points()
            for ap_dict in ap_list:
                ap_str += "+WLIST: "
                ap_str += f"{ap_dict['ssid']},"
                ap_str += f"{ap_dict['hwAddress']},"
                ap_str += f"{ap_dict['strength']},"
                ap_str += f"{ap_dict['maxBitrate']},"
                ap_str += f"{ap_dict['frequency']},"
                ap_str += f"{ap_dict['flags']},"
                ap_str += f"{ap_dict['wpaFlags']},"
                ap_str += f"{ap_dict['rsnFlags']},"
                ap_str += f"{ap_dict['lastSeen']},"
                ap_str += f"{ap_dict['security']},"
                ap_str += f"{ap_dict['keymgmt']}\r\n"
            return (True, f"{ap_str}OK")
        except Exception as exception:
            syslog(LOG_ERR, f"Error listing wifi access points: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in WifiListCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param == ""
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+WLIST"

    @staticmethod
    def signature() -> str:
        return WifiListCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return WifiListCommand.NAME
