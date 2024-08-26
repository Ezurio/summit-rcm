#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
File that consists of the Power Command Functionality
"""
from syslog import LOG_ERR, syslog
from typing import List, Tuple
from enum import IntEnum
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.definition import PowerStateEnum
from summit_rcm.services.system_service import SystemService


class States(IntEnum):
    on = 0
    off = 1
    suspend = 2
    reboot = 3


class PowerCommand(Command):
    """
    AT Command to set the power state
    """

    NAME: str = "Power"
    SIGNATURE: str = "at+power"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = PowerCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            await SystemService().set_power_state(PowerStateEnum(params_dict["state"]))
            return (True, "OK")
        except Exception as exception:
            syslog(LOG_ERR, f"Error while setting the power state: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        given_num_param = len(params_list)
        valid &= given_num_param in PowerCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if not valid:
            return (False, {})
        try:
            params_dict["state"] = States(int(params_list[0])).name
        except ValueError:
            valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+POWER=<state>"

    @staticmethod
    def signature() -> str:
        return PowerCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return PowerCommand.NAME
