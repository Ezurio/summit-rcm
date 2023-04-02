from dataclasses import dataclass
from typing import Tuple
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.connection_service import ConnectionService


@dataclass
class CIPSTARTCommand(Command):
    name = "Start IP connection"
    signature = "at+cipstart"
    valid_num_params = [4, 5]

    @staticmethod
    def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = CIPSTARTCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {CIPSTARTCommand.signature}?\r\n",
            )
        params_dict["type"] = ConnectionService.parse_connection_type(
            params_dict["type"]
        )
        if params_dict["type"] is None:
            return (True, f"\r\nCONNECTION TYPE {params_dict[type]} ERROR\r\n")

        if ConnectionService().start_connection(
            id=params_dict["connection_id"],
            type=params_dict["type"],
            addr=params_dict["remote_ip"],
            port=params_dict["remote_port"],
            keepalive=params_dict["keepalive"],
        ):
            return (True, "\r\nOK\r\n")
        else:
            return (True, "\r\nCONNECTION START ERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        given_num_param = len(params_list)
        valid &= given_num_param in CIPSTARTCommand.valid_num_params
        for param in params_list:
            valid &= param != ""
        if valid:
            try:
                params_dict["connection_id"] = int(params_list[0])
                params_dict["type"] = params_list[1]
                params_dict["remote_ip"] = params_list[2]
                params_dict["remote_port"] = params_list[3]
                params_dict["keepalive"] = (
                    int(params_list[4]) if given_num_param == 5 else 0
                )
            except Exception:
                valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return (
            "\r\nAT+CIPSTART=<connection id>,<type>,<remote IP>,"
            "<remote port>[,<keepalive>]\r\n"
        )
