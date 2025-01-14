#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
AT interface's finite state machine module
"""
import importlib
import pkgutil
from syslog import syslog, LOG_ERR
from typing import Callable, List, Optional, Tuple
from asyncio import Transport, Protocol
from threading import Lock
from transitions.extensions.asyncio import AsyncMachine
from summit_rcm.utils import Singleton
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.commands.communication_check_command import (
    CommunicationCheckCommand,
)
from summit_rcm.at_interface.commands.empty_command import EmptyCommand
from summit_rcm.at_interface.commands.version_command import VersionCommand
from summit_rcm.at_interface.commands.cip_start_command import CIPStartCommand
from summit_rcm.at_interface.commands.cip_send_command import CIPSendCommand
from summit_rcm.at_interface.commands.cip_close_command import CIPCloseCommand
from summit_rcm.at_interface.commands.cip_configure_ssl_command import CIPConfigureSSL
from summit_rcm.at_interface.commands.ping_command import PingCommand
from summit_rcm.at_interface.commands.connection_list_command import (
    ConnectionListCommand,
)
from summit_rcm.at_interface.commands.power_command import PowerCommand
from summit_rcm.at_interface.commands.factory_reset_command import FactoryResetCommand
from summit_rcm.at_interface.commands.fips_command import FipsCommand
from summit_rcm.at_interface.commands.connection_activate_command import (
    ConnectionActivateCommand,
)
from summit_rcm.at_interface.commands.http_configure_transaction import (
    HTTPConfigureTransaction,
)
from summit_rcm.at_interface.commands.http_execute_transaction import (
    HTTPExecuteTransaction,
)
from summit_rcm.at_interface.commands.http_add_header import HTTPAddHeader
from summit_rcm.at_interface.commands.http_enable_reponse_headers import (
    HTTPEnableResponseHeader,
)
from summit_rcm.at_interface.commands.http_clear_configuration import (
    HTTPClearConfiguration,
)
from summit_rcm.at_interface.commands.http_configure_ssl import HTTPConfigureSSL
from summit_rcm.at_interface.commands.network_interface_statistics import (
    NetworkInterfaceStatisticsCommand,
)
from summit_rcm.at_interface.commands.network_interface_driver_info import (
    NetworkInterfaceDriverInfoCommand,
)
from summit_rcm.at_interface.commands.network_interfaces_command import (
    NetworkInterfacesCommand,
)
from summit_rcm.at_interface.commands.connection_modify_command import (
    ConnectionModifyCommand,
)
from summit_rcm.at_interface.commands.network_virtual_interface_command import (
    NetworkVirtualInterfaceCommand,
)
from summit_rcm.at_interface.commands.wifi_list_command import WifiListCommand
from summit_rcm.at_interface.commands.wifi_scan_command import WifiScanCommand
from summit_rcm.at_interface.commands.datetime_command import DatetimeCommand
from summit_rcm.at_interface.commands.timezone_set_command import TimezoneSetCommand
from summit_rcm.at_interface.commands.timezone_get_command import TimezoneGetCommand
from summit_rcm.at_interface.commands.certificates_get_command import (
    CertificatesGetCommand,
)
from summit_rcm.at_interface.commands.wifi_enabled_command import WiFiEnabledCommand
from summit_rcm.at_interface.commands.wifi_hardware_command import WiFiHardwareCommand
from summit_rcm.at_interface.commands.files_delete_command import FilesDeleteCommand
from summit_rcm.at_interface.commands.files_export_command import FilesExportCommand
from summit_rcm.at_interface.commands.files_list_command import FilesListCommand
from summit_rcm.at_interface.commands.files_upload_command import FilesUploadCommand
from summit_rcm.at_interface.commands.fwupdate_run_command import FWUpdateRunCommand
from summit_rcm.at_interface.commands.fwupdate_send_command import FWUpdateSendCommand
from summit_rcm.at_interface.commands.fwupdate_status_command import (
    FWUpdateStatusCommand,
)
from summit_rcm.at_interface.commands.log_get_command import LogGetCommand
from summit_rcm.at_interface.commands.log_debug_level_command import (
    LogDebugLevelCommand,
)
from summit_rcm.at_interface.commands.at_echo_disable_command import (
    ATEchoDisableCommand,
)
from summit_rcm.at_interface.commands.at_echo_enable_command import ATEchoEnableCommand

discovered_plugins = {
    name: importlib.import_module(name)
    for finder, name, ispkg in pkgutil.iter_modules()
    if name.startswith("summit_rcm_")
}


AT_COMMANDS: List[Command] = [
    CIPStartCommand,
    CIPCloseCommand,
    CIPSendCommand,
    CIPConfigureSSL,
    CommunicationCheckCommand,
    EmptyCommand,
    VersionCommand,
    PingCommand,
    ConnectionListCommand,
    PowerCommand,
    FactoryResetCommand,
    FipsCommand,
    ConnectionActivateCommand,
    HTTPConfigureTransaction,
    HTTPExecuteTransaction,
    HTTPAddHeader,
    HTTPEnableResponseHeader,
    HTTPClearConfiguration,
    HTTPConfigureSSL,
    NetworkInterfaceStatisticsCommand,
    NetworkInterfaceDriverInfoCommand,
    NetworkInterfacesCommand,
    ConnectionModifyCommand,
    NetworkVirtualInterfaceCommand,
    WifiListCommand,
    WifiScanCommand,
    DatetimeCommand,
    TimezoneSetCommand,
    TimezoneGetCommand,
    CertificatesGetCommand,
    WiFiEnabledCommand,
    WiFiHardwareCommand,
    FilesDeleteCommand,
    FilesExportCommand,
    FilesListCommand,
    FilesUploadCommand,
    FWUpdateRunCommand,
    FWUpdateSendCommand,
    FWUpdateStatusCommand,
    LogGetCommand,
    LogDebugLevelCommand,
    ATEchoDisableCommand,
    ATEchoEnableCommand,
]

for plugin in discovered_plugins:
    try:
        at_commands = discovered_plugins[plugin].get_at_commands()
        if at_commands:
            AT_COMMANDS.extend(at_commands)
    except Exception:
        continue


class ATInterfaceFSM(metaclass=Singleton):
    """
    The AT command interface finite state machine
    """

    states = ["idle", "analyze_input", "validate_command", "process_command"]
    machine: Optional[AsyncMachine] = None

    mutex = Lock()

    # State-holding data members
    _command_buffer: str = ""
    _current_command: Command = None
    _current_command_params: str = ""
    _current_command_print_usage: bool = False

    debug = False
    echo_enabled: bool = False

    _listeners: Callable[[str], None] = []

    _transport: Optional[Transport] = None
    _protocol: Optional[Protocol] = None

    _closing: bool = False

    def __init__(self):
        self.machine = AsyncMachine(model=self, states=self.states, initial="idle")
        self.machine.add_transition(
            trigger="input_received", source="idle", dest="analyze_input"
        )
        self.machine.add_transition(
            trigger="input_received", source="analyze_input", dest="analyze_input"
        )
        self.machine.add_transition(
            trigger="input_received", source="validate_command", dest="validate_command"
        )
        self.machine.add_transition(
            trigger="input_received", source="process_command", dest="process_command"
        )
        self.machine.add_transition(
            trigger="carriage_return_found",
            source="analyze_input",
            dest="validate_command",
        )
        self.machine.add_transition(
            trigger="carriage_return_not_found",
            source="analyze_input",
            dest="idle",
        )
        self.machine.add_transition(
            trigger="valid_command",
            source="validate_command",
            dest="process_command",
        )
        self.machine.add_transition(
            trigger="invalid_command",
            source="validate_command",
            dest="idle",
        )
        self.machine.add_transition(
            trigger="command_complete",
            source="process_command",
            dest="idle",
        )

    def close(self):
        """Close the state machine"""
        self._closing = True
        if self._transport:
            self._transport.close()

    async def on_input_received(self, message: bytes | str):
        if isinstance(message, str):
            message = bytes(message)
        if self.state == "idle" or self.state == "analyze_input":
            try:
                message = message.decode("utf-8")
                length = len(self.command_buffer)
                self.command_buffer += message
                while "\x7f" in self.command_buffer:
                    if length > 1:
                        backspace_index = self.command_buffer.find("\x7f")
                        temp_buf = self.command_buffer[: backspace_index - 1]
                        if backspace_index != (length - 1):
                            temp_buf += self.command_buffer[backspace_index + 1 :]
                        self.command_buffer = temp_buf
                    else:
                        self.command_buffer = ""
                self.echo(message)
            except UnicodeDecodeError as exception:
                syslog(LOG_ERR, f"Invalid Character Received: {str(exception)}")
        elif self.state == "process_command":
            self.log_debug("Rx: " + str(message) + " ")
            for listener in self._listeners:
                listener(message)
        await self.input_received()

    async def on_enter_idle(self):
        self.log_debug("Entering Idle\r\n")

    async def on_enter_analyze_input(self):
        self.log_debug("Entering Analyze Input\r\n")
        current_buffer = self.command_buffer
        found_crlf = len(current_buffer) >= 1 and current_buffer[-1:] == "\r"
        if found_crlf:
            await self.carriage_return_found()
        else:
            await self.carriage_return_not_found()

    async def on_enter_validate_command(self):
        self.log_debug("Entering Validate Command\r\n")
        command = ""
        command = self.command_buffer.strip()

        (command_to_run, params_to_use, print_usage) = self.lookup_command(command)
        if command_to_run is None:
            self.current_command = None
            self.at_output("ERROR")
            await self.invalid_command()
            return

        self.current_command = command_to_run
        self.current_command_params = params_to_use
        self.current_command_print_usage = print_usage
        await self.valid_command()

    async def on_exit_validate_command(self):
        self.clear_command_buffer()

    async def on_enter_process_command(self):
        self.log_debug("Entering Process Command\r\n")

        command = self.current_command
        params = self.current_command_params
        print_usage = self.current_command_print_usage

        self.log_debug(
            f"*** EXEC: id: {command.signature()}, name: {command.name()}, "
            f"params: {params}, print usage: {print_usage} ***\r\n"
        )
        done = True
        if print_usage:
            resp = str(command.usage())
        else:
            (done, resp) = await command.execute(params)
        self.log_debug(f"*** RESP: {resp} ***\r\n")
        self.at_output(resp)

        if done:
            self.current_command = None
            self.current_command_params = ""
            self.current_command_print_usage = False
            await self.command_complete()

    def lookup_command(self, command: str) -> Tuple[Optional[Command], str, bool]:
        """
        Looks up the given command input aginst the dictionary of valid, supported AT commands
        """
        self.log_debug(f"Looking up command for: {command}\r\n")

        # Check for an empty command
        if command == "":
            return (EmptyCommand, "", False)

        command_lower = command.lower()

        # Check for a valid command prefix
        if not command_lower.startswith("at"):
            return (None, "", False)

        print_usage = command_lower.endswith("?")
        if print_usage:
            command = command.rstrip(command[-1])
        if "=" in command:
            # 'value' command
            command_split = command.split("=")
            for at_command in AT_COMMANDS:
                if command_split[0].lower() == at_command.signature():
                    return (at_command, "=".join(command_split[1:]), print_usage)
        else:
            # not a 'value' command
            for at_command in AT_COMMANDS:
                if command_lower == at_command.signature():
                    return (at_command, "", print_usage)
        return (None, "", False)

    def at_output(
        self,
        c,
        print_leading_line_break: bool = True,
        print_trailing_line_break: bool = True,
    ):
        if self._transport and len(c) > 0:
            if isinstance(c, str):
                c = bytes(c, "utf-8")
            if print_leading_line_break:
                c = bytes("\r\n", "utf-8") + c
            if print_trailing_line_break:
                c = c + bytes("\r\n", "utf-8")
            if not self._closing:
                self._transport.write(c)

    def log_debug(self, msg):
        if self.debug:
            self.at_output(f"DBG: {str(msg)}", False, False)

    def echo(self, msg):
        if self.echo_enabled:
            self.at_output(str(msg), False, False)

    def enable_echo(self, enabled: bool):
        self.echo_enabled = enabled

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
