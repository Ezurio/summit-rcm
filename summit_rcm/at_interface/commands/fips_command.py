#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
File that consists of the Fips Command Functionality
"""
from syslog import LOG_ERR, syslog
from typing import List, Tuple
from enum import IntEnum
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.definition import PowerStateEnum
from summit_rcm.services.fips_service import FipsService, FipsUnsupportedError
from summit_rcm.services.system_service import SystemService


class States(IntEnum):
    fips = 0
    fips_wifi = 1
    unset = 2


class FipsCommand(Command):
    """
    AT Command to get/set fips state
    """

    NAME: str = "Fips"
    SIGNATURE: str = "at+fips"
    VALID_NUM_PARAMS: List[int] = [1, 2]
    VALID_STATE_VAL: List[str] = ["fips", "fips_wifi", "unset"]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = FipsCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            if params_dict["state"]:
                if await FipsService().get_fips_state() == "unsupported":
                    raise FipsUnsupportedError("Fips Unsupported")
                success = await FipsService().set_fips_state(params_dict["state"])
                if not success:
                    return (True, "ERROR")
                if params_dict["reboot"]:
                    await SystemService().set_power_state(PowerStateEnum.REBOOT)
                return (True, "OK")
            else:
                fips_str = await FipsService().get_fips_state()
            return (True, f"+FIPS: {fips_str}\r\nOK")
        except Exception as exception:
            syslog(LOG_ERR, f"Error setting/getting FIPS state: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        given_num_param = len(params_list)
        valid &= given_num_param in FipsCommand.VALID_NUM_PARAMS
        if not valid:
            return (False, {})
        try:
            params_dict["state"] = (
                States(int(params_list[0])).name if params_list[0] else ""
            )
            if params_dict["state"] and given_num_param < 2:
                raise ValueError
            params_dict["reboot"] = (
                bool(int(params_list[1])) if given_num_param > 1 and params_list[1] else False
            )
        except ValueError:
            valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+FIPS[=<state>[,<reboot>]]"

    @staticmethod
    def signature() -> str:
        return FipsCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return FipsCommand.NAME
