from typing import List, Tuple
from summit_rcm.at_interface.commands.command import Command
from pythonping import ping

DEFAULT_TIMEOUT = 5
PING_COUNT = 3


class PingCommand(Command):
    NAME: str = "Ping"
    SIGNATURE: str = "at+ping"
    VALID_NUM_PARAMS: List[int] = [1, 2]

    @staticmethod
    def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = PingCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {PingCommand.SIGNATURE}?\r\n",
            )
        try:
            ping_str = str(
                ping(
                    params_dict["target"],
                    verbose=True,
                    timeout=params_dict["timeout"],
                    count=PING_COUNT,
                )
            )
            return (True, f"\r\n{ping_str}\r\n")
        except Exception as e:
            print(f"Error: {str(e)}")
            return (True, "\r\nError\r\n")

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
                    int(params_list[1]) if given_num_param == 2 else DEFAULT_TIMEOUT
                )
            except Exception:
                valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+PING=<target>[,<timeout>]\r\n"

    @staticmethod
    def signature() -> str:
        return PingCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return PingCommand.NAME
