import serial
from typing import Callable, Optional, Tuple
from statemachine import StateMachine, State
from threading import Lock
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.commands.communication_check_command import (
    CommunicationCheckCommand,
)
from summit_rcm.at_interface.commands.empty_command import EmptyCommand
from summit_rcm.at_interface.commands.version_command import VersionCommand
from summit_rcm.at_interface.commands.cipstart_command import CIPSTARTCommand
from summit_rcm.at_interface.commands.cipsend_command import CIPSENDCommand
from summit_rcm.at_interface.commands.cipclose_command import CIPCLOSECommand
from utils import Singleton

AT_COMMANDS = {
    CIPSTARTCommand.signature: CIPSTARTCommand,
    CIPCLOSECommand.signature: CIPCLOSECommand,
    CIPSENDCommand.signature: CIPSENDCommand,
    CommunicationCheckCommand.signature: CommunicationCheckCommand,
    EmptyCommand.signature: EmptyCommand,
    VersionCommand.signature: VersionCommand,
}


class SingletonBase(metaclass=Singleton):
    pass


class SingletonStateMachineMeta(type(StateMachine), type(SingletonBase)):
    pass


class ATInterfaceFSM(StateMachine, SingletonBase, metaclass=SingletonStateMachineMeta):
    """
    The AT command interface finite state machine
    """

    # States
    idle = State("Idle", initial=True)
    analyze_input = State("Analyze Input")
    validate_command = State("Validate Command")
    process_command = State("Process Command")

    # Events
    input_received = (
        idle.to(analyze_input)
        | analyze_input.to(analyze_input)
        | validate_command.to(validate_command)
        | process_command.to(process_command)
    )
    carriage_return_found = analyze_input.to(validate_command)
    carriage_return_not_found = analyze_input.to(idle)
    valid_command = validate_command.to(process_command)
    invalid_command = validate_command.to(idle)
    command_complete = process_command.to(idle)

    mutex = Lock()

    # State-holding data members
    _command_buffer: str = ""
    _current_command: Command = None
    _current_command_params: str = ""
    _current_command_print_usage: bool = False

    debug = False
    echo = True

    _listeners: Callable[[str], None] = []

    def __init__(self, model=None, state_field="state", start_value=None):
        self.quit = False
        self.dte_file = serial.Serial("/dev/ttyS2", 115200, timeout=0)
        super().__init__(model, state_field, start_value)

    def on_input_received(
        self, event: str, source: State, target: State, message: bytes
    ):
        if source.id == self.idle.id or source.id == self.analyze_input.id:
            message = message.decode("utf-8")
            self.command_buffer += message
            self.echo(message)
        elif source.id == self.process_command.id:
            for listener in self._listeners:
                listener(message)

    def on_invalid_command(
        self, event: str, source: State, target: State, message: str = ""
    ):
        self.dte_output("\r\nERROR\r\n")

    def on_enter_idle(self):
        self.log_debug("Entering Idle\r\n")

    def on_enter_analyze_input(self):
        self.log_debug("Entering Analyze Input\r\n")
        current_buffer = self.command_buffer
        found_crlf = len(current_buffer) >= 1 and current_buffer[-1:] == "\r"
        if found_crlf:
            self.carriage_return_found()
        else:
            self.carriage_return_not_found()

    def on_enter_validate_command(self):
        self.log_debug("Entering Validate Command\r\n")
        command = ""
        command = self.command_buffer.strip()

        (command_to_run, params_to_use, print_usage) = self.lookup_command(command)
        if command_to_run is None:
            self.current_command = None
            self.invalid_command()
            return

        self.current_command = command_to_run
        self.current_command_params = params_to_use
        self.current_command_print_usage = print_usage
        self.valid_command()

    def on_exit_validate_command(self):
        self.clear_command_buffer()

    def on_enter_process_command(self):
        self.log_debug("Entering Process Command\r\n")

        command = self.current_command
        params = self.current_command_params
        print_usage = self.current_command_print_usage

        if command is None:
            self.dte_output("Error processing command!\r\n")
            self.current_command = None
            self.current_command_params = ""
            self.current_command_print_usage = False
            self.command_complete()
            return

        self.log_debug(
            f"*** EXEC: id: {command.signature}, name: {command.name}, params: {params}, print usage: {print_usage} ***\r\n"
        )
        done = True
        if print_usage:
            resp = str(command.usage())
        else:
            (done, resp) = command.execute(params)
        self.log_debug(f"*** RESP: {resp} ***\r\n")
        self.dte_output(resp)

        if done:
            self.current_command = None
            self.current_command_params = ""
            self.current_command_print_usage = False
            self.command_complete()

    def lookup_command(self, command: str) -> Tuple[Optional[Command], str, bool]:
        """
        Looks up the given command input aginst the dictionary of valid, supported AT commands
        """
        self.log_debug(f"Looking up command for: {command}\r\n")

        # Check for an empty command
        if command == "":
            return (EmptyCommand, "", False)

        # Check for a valid command prefix
        if not command.lower().startswith("at"):
            return (None, "", False)

        command = command.lower()
        print_usage = command.lower().endswith("?")
        if print_usage:
            command = command.rstrip(command[-1])
        if "=" in command:
            # 'value' command
            command_split = command.split("=")
            if command_split[0] in AT_COMMANDS.keys():
                return (
                    AT_COMMANDS[command_split[0]],
                    "=".join(command_split[1:]),
                    print_usage,
                )
            else:
                return (None, "", False)
        else:
            # not a 'value' command
            if command in AT_COMMANDS.keys():
                return (AT_COMMANDS[command], "", print_usage)
            else:
                return (None, "", False)

    def check_escape(self):
        pass

    def dte_input(self, c):
        self.input_received(message=c)

    def dte_output(self, c):
        try:
            self.dte_file.write(c)
        except TypeError:
            self.dte_file.write(bytes(c, "utf-8"))
        self.dte_file.flush()

    def log_debug(self, msg):
        if self.debug:
            self.dte_output(f"DBG: {str(msg)}")

    def echo(self, msg):
        if self.echo:
            self.dte_output(str(msg))

    def register_listener(self, listener: Callable[[str], None]) -> int:
        self._listeners.append(listener)
        return len(self._listeners) - 1

    def deregister_listener(self, id: int):
        del self._listeners[id]

    @property
    def command_buffer(self):
        with self.mutex:
            return self._command_buffer

    @command_buffer.setter
    def command_buffer(self, value: str):
        with self.mutex:
            self._command_buffer = value

    def clear_command_buffer(self):
        self.command_buffer = ""

    @property
    def current_command(self):
        with self.mutex:
            return self._current_command

    @current_command.setter
    def current_command(self, value: Optional[Command]):
        with self.mutex:
            self._current_command = value

    @property
    def current_command_params(self):
        with self.mutex:
            return self._current_command_params

    @current_command_params.setter
    def current_command_params(self, value: str):
        with self.mutex:
            self._current_command_params = value

    @property
    def current_command_print_usage(self):
        with self.mutex:
            return self._current_command_print_usage

    @current_command_print_usage.setter
    def current_command_print_usage(self, value: bool):
        with self.mutex:
            self._current_command_print_usage = value
