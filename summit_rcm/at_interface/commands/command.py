from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple


@dataclass
class Command(ABC):
    name: str
    signature: str

    @staticmethod
    @abstractmethod
    def execute(params: str) -> Tuple[bool, str]:
        """
        Function which runs the actual logic of the command. Return type is a tuple in the form
        (done, response)
        """
        pass

    @staticmethod
    @abstractmethod
    def usage() -> str:
        """
        Returns the expected usage of the command
        """
        pass
