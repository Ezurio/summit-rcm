#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
File that consists of the ATEchoDisable Command Functionality
"""
from syslog import LOG_ERR, syslog
from typing import List, Tuple
from summit_rcm.at_interface.commands.command import Command
import summit_rcm.at_interface.fsm as fsm


class ATEchoDisableCommand(Command):
    """
    AT Command to disable the AT Interface's serial echo
    """

    NAME: str = "Disable AT Serial Echo"
    SIGNATURE: str = "ate0"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = ATEchoDisableCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        fsm.ATInterfaceFSM().enable_echo(False)
        return (True, "OK")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in ATEchoDisableCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param == ""
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "ATE0"

    @staticmethod
    def signature() -> str:
        return ATEchoDisableCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return ATEchoDisableCommand.NAME
