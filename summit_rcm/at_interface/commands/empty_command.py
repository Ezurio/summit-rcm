from dataclasses import dataclass
from typing import Tuple
from summit_rcm.at_interface.commands.command import Command


@dataclass
class EmptyCommand(Command):
    name = "Empty"
    signature = ""

    @staticmethod
    def execute(params: str) -> Tuple[bool, str]:
        return (True, "\r\n")

    @staticmethod
    def usage() -> str:
        return "\r\n"
