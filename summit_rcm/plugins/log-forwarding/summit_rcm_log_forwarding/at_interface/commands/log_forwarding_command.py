#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
File that consists of the LogForwarding Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from enum import IntEnum
from summit_rcm.at_interface.commands.command import Command
from summit_rcm_log_forwarding.services.log_forwarding_service import (
    LogForwardingService,
)


class Types(IntEnum):
    inactive = 0
    active = 1


class States(IntEnum):
    active = 0
    reloading = 1
    inactive = 2
    failed = 3
    activating = 4
    deactivated = 5
    unknown = 6


class LogForwardingCommand(Command):
    """
    AT Command to set the state of the log forwarding service
    """

    NAME: str = "Set Log Forwarding State"
    SIGNATURE: str = "at+logfwd"
    VALID_NUM_PARAMS: List[int] = [1]
    DEVICE_TYPE: str = ""

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = LogForwardingCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            if params_dict["state"]:
                await LogForwardingService().set_state(params_dict["state"])
                return (True, "OK")
            response = States[await LogForwardingService().get_active_state()]
            return (True, f"+LOGFWD: {response}\r\nOK")
        except Exception as exception:
            err_msg = str(exception) if str(exception) else exception.__class__.__name__
            syslog(LOG_ERR, f"Error setting log forwarding state: {err_msg}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in LogForwardingCommand.VALID_NUM_PARAMS
        if not valid:
            return (False, {})
        try:
            params_dict["state"] = (
                Types(int(params_list[0])).name if params_list[0] else ""
            )
        except ValueError:
            return (False, params_dict)
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+LOGFWD[=<state>]"

    @staticmethod
    def signature() -> str:
        return LogForwardingCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return LogForwardingCommand.NAME
