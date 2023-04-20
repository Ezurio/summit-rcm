from typing import List, Tuple
from summit_rcm.at_interface.commands.command import Command


class EmptyCommand(Command):
    NAME: str = "Empty"
    SIGNATURE: str = ""
    VALID_NUM_PARAMS: List[int] = [0]

    @staticmethod
    def execute(params: str) -> Tuple[bool, str]:
        return (True, "\r\n")

    @staticmethod
    def usage() -> str:
        return "\r\n"

    @staticmethod
    def signature() -> str:
        return EmptyCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return EmptyCommand.NAME
