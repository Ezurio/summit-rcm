from dataclasses import dataclass
from typing import Tuple
from summit_rcm.at_interface.commands.command import Command


@dataclass
class CommunicationCheckCommand(Command):
    name = "Communication Check"
    signature = "at"

    @staticmethod
    def execute(params: str) -> Tuple[bool, str]:
        return (True, "\r\nOK\r\n")

    @staticmethod
    def usage() -> str:
        return "\r\nAT\r\n"
