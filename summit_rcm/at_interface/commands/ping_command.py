from typing import List, Tuple
from summit_rcm.at_interface.commands.command import Command
import subprocess
import re

DEFAULT_TIMEOUT = "10"
DEFAULT_PROTOCOL = ""
PING_COUNT = 1


class PingCommand(Command):
    NAME: str = "Ping"
    SIGNATURE: str = "at+ping"
    VALID_NUM_PARAMS: List[int] = [1, 2, 3]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = PingCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {PingCommand.SIGNATURE}?\r\n",
            )
        command = [
            "ping",
            "-c",
            str(PING_COUNT),
            "-W",
            params_dict["timeout"],
            params_dict["target"],
        ]
        if params_dict["protocol"]:
            protocol = "-" + params_dict["protocol"]
            command.insert(1, protocol)
        try:
            proc = subprocess.run(command, capture_output=True)
            ping_str = proc.stdout.decode("utf-8")
            match = re.search(r"\d+\.\d+/(\d+\.\d+)/\d+\.\d+", ping_str)
            if match:
                ping_str = match.group(1)
                return (True, f"\r\n{ping_str} OK\r\n")
            else:
                return (True, "\r\nTIMEOUT ERROR\r\n")
        except Exception:
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        given_num_param = len(params_list)
        valid &= given_num_param in PingCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if valid:
            try:
                params_dict["target"] = params_list[0]
                params_dict["timeout"] = (
                    params_list[1] if given_num_param > 1 else DEFAULT_TIMEOUT
                )
                params_dict["protocol"] = (
                    params_list[2] if given_num_param == 3 else DEFAULT_PROTOCOL
                )
            except Exception:
                valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+PING=<target>[,<timeout>[,<protocol>]]\r\n"

    @staticmethod
    def signature() -> str:
        return PingCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return PingCommand.NAME
