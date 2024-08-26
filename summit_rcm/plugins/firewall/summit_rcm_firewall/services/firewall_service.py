#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to support iptables firewall configuration
"""

import json
import os
from syslog import syslog, LOG_ERR
from typing import List, Tuple
import asyncio
try:
    import aiofiles
except ImportError as error:
    # Ignore the error if the aiofiles module is not available if generating documentation
    if os.environ.get("DOCS_GENERATION") != "True":
        raise error
from summit_rcm.utils import Singleton

IPTABLES = "/usr/sbin/iptables"
IP6TABLES = "/usr/sbin/ip6tables"
FORWARDED_PORTS_FILE = "/tmp/summit-rcm.ports"
ADD_PORT = "addForwardPort"
REMOVE_PORT = "removeForwardPort"
PORT_COMMANDS = [ADD_PORT, REMOVE_PORT]
WIFI_INTERFACE = "wlan0"
IPV4 = "ipv4"
IPV6 = "ipv6"
IPV4V6 = "ipv4v6"
IP_VERSIONS = [IPV4, IPV6]


class ForwardedPort:
    """Data class helper for working with forwarded ports"""

    def __init__(
        self, port: int, protocol: str, toport: str, toaddr: str, ip_version: str = IPV4
    ) -> None:
        self.port = port
        self.protocol = protocol
        self.toport = toport
        self.toaddr = toaddr
        self.ip_version = ip_version

    def __eq__(self, __value: object) -> bool:
        """Determine whether or not this forwarded port is equal to the provided object (__value)"""
        return (
            isinstance(__value, ForwardedPort)
            and self.port == __value.port
            and self.protocol == __value.protocol
            and self.toport == __value.toport
            and self.toaddr == __value.toaddr
            and self.ip_version == __value.ip_version
        )

    def to_json(self, is_legacy: bool = False):
        """Return the JSON representation of the forwarded port"""
        return {
            "port": self.port,
            "protocol": self.protocol,
            "toport": self.toport,
            "toaddr": self.toaddr,
            "ip_version" if is_legacy else "ipVersion": self.ip_version,
        }


class FirewallService(metaclass=Singleton):
    """
    iptables-based wrapper to support basic firewall control (i.e., port forwarding)
    """

    def __init__(self):
        self.forwarded_ports: List[ForwardedPort] = []
        self.load_forwarded_ports()

    def load_forwarded_ports(self) -> None:
        """
        Load the list of forwarded ports from disk
        """
        try:
            self.forwarded_ports = []
            if os.path.exists(FORWARDED_PORTS_FILE):
                with open(FORWARDED_PORTS_FILE, "r") as forwarded_ports_file:
                    forwarded_ports: list = json.loads(forwarded_ports_file.read())
                    for port in forwarded_ports:
                        if not isinstance(port, dict):
                            continue
                        self.forwarded_ports.append(
                            ForwardedPort(
                                port["port"],
                                port["protocol"],
                                port["toport"],
                                port["toaddr"],
                                port[
                                    "ipVersion"
                                    if "ipVersion" in port.keys()
                                    else "ip_version"
                                ],
                            )
                        )
        except Exception as exception:
            self.log_exception(exception, "Unable to load forwarded ports")
            self.forwarded_ports = []

    async def save_forwarded_ports(self) -> None:
        """
        Save the list of forwarded ports to disk
        """
        try:
            async with aiofiles.open(FORWARDED_PORTS_FILE, "w") as forwarded_ports_file:
                forwarded_ports_json = []
                for port in self.forwarded_ports:
                    forwarded_ports_json.append(port.to_json())
                await forwarded_ports_file.write(json.dumps(forwarded_ports_json))
        except Exception as exception:
            self.log_exception(exception, "Unable to save forwarded ports")

    @staticmethod
    def log_exception(exception, message: str = "") -> None:
        """
        Log an exception
        """
        syslog(LOG_ERR, message + str(exception))

    def forwarded_port_is_present(self, port_to_analyze: ForwardedPort) -> bool:
        """
        Determine whether or not the port, as represented by the passed-in arguments, is currently
        being forwarded
        """
        for forwarded_port in self.forwarded_ports:
            if forwarded_port == port_to_analyze:
                return True
        return False

    async def configure_forwarded_port(
        self, command: str, forwarded_port: ForwardedPort
    ) -> Tuple[bool, str]:
        """
        Add/remove forwarded port.

        Return value is a tuple in the form of: (success, message)
        """
        # Check if a forwarded port is already present with the given parameters and exit early if
        # appropriate.
        forwarded_port_present: bool = self.forwarded_port_is_present(forwarded_port)
        if command == ADD_PORT and forwarded_port_present:
            return (True, "Forwarded port already exists")
        if command == REMOVE_PORT and not forwarded_port_present:
            return (True, "Forwarded port doesn't exist")

        # Add/remove PREROUTING rule
        proc = await asyncio.create_subprocess_exec(
            *[
                IPTABLES if forwarded_port.ip_version == IPV4 else IP6TABLES,
                "-t",
                "nat",
                "-A" if command == ADD_PORT else "-D",
                "PREROUTING",
                "-p",
                forwarded_port.protocol,
                "-i",
                WIFI_INTERFACE,
                "--dport",
                forwarded_port.port,
                "-j",
                "DNAT",
                "--to-destination",
                f"{forwarded_port.toaddr}:{forwarded_port.toport}"
                if forwarded_port.ip_version == IPV4
                else f"[{forwarded_port.toaddr}]:{forwarded_port.toport}",
            ],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            msg = (
                f"Error {'adding' if command == ADD_PORT else 'removing'}: "
                f"{stderr.decode('utf-8').strip()}"
            )
            syslog(LOG_ERR, msg)
            return (False, msg)

        # Add/remove FORWARD rule
        proc = await asyncio.create_subprocess_exec(
            *[
                IPTABLES if forwarded_port.ip_version == IPV4 else IP6TABLES,
                "-A" if command == ADD_PORT else "-D",
                "FORWARD",
                "-p",
                forwarded_port.protocol,
                "-d",
                forwarded_port.toaddr,
                "--dport",
                forwarded_port.toport,
                "-m",
                "state",
                "--state",
                "NEW",
                "-j",
                "ACCEPT",
            ],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            msg = (
                f"Error {'adding' if command == ADD_PORT else 'removing'}: "
                f"{stderr.decode('utf-8').strip()}"
            )
            syslog(LOG_ERR, msg)
            return (False, msg)

        # Update stored list of forwarded ports
        if command == ADD_PORT:
            self.forwarded_ports.append(forwarded_port)
        else:
            self.forwarded_ports[:] = [
                x for x in self.forwarded_ports if x != forwarded_port
            ]
        await self.save_forwarded_ports()

        return (True, "")

    @staticmethod
    async def open_port(port: str, ip_version: str = IPV4V6):
        """
        Open a port in the firewall
        """
        commands = []
        if ip_version == IPV4V6:
            commands.append(IPTABLES)
            commands.append(IP6TABLES)
        elif ip_version == IPV4:
            commands.append(IPTABLES)
        elif ip_version == IPV6:
            commands.append(IP6TABLES)
        else:
            syslog(LOG_ERR, f"open_port: invalid IP version provided: '{ip_version}'")
            return

        try:
            for command in commands:
                proc = await asyncio.create_subprocess_exec(
                    *[
                        command,
                        "-I",
                        "INPUT",
                        "-p",
                        "tcp",
                        "--dport",
                        port,
                        "-j",
                        "ACCEPT",
                    ],
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await proc.communicate()
                if proc.returncode != 0:
                    msg = f"Error opening port {port}: {stderr.decode('utf-8').strip()}"
                    syslog(LOG_ERR, msg)
                    return
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to open firewall port: {str(exception)}")

    @staticmethod
    async def close_port(port: str, ip_version: str = IPV4V6):
        """
        Close a port in the firewall
        """
        commands = []
        if ip_version == IPV4V6:
            commands.append(IPTABLES)
            commands.append(IP6TABLES)
        elif ip_version == IPV4:
            commands.append(IPTABLES)
        elif ip_version == IPV6:
            commands.append(IP6TABLES)
        else:
            syslog(LOG_ERR, f"close_port: invalid IP version provided: '{ip_version}'")
            return

        try:
            for command in commands:
                proc = await asyncio.create_subprocess_exec(
                    *[
                        command,
                        "-D",
                        "INPUT",
                        "-p",
                        "tcp",
                        "--dport",
                        port,
                        "-j",
                        "ACCEPT",
                    ],
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await proc.communicate()
                if proc.returncode != 0:
                    msg = f"Error closing port {port}: {stderr.decode('utf-8').strip()}"
                    syslog(LOG_ERR, msg)
                    return
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to close firewall port: {str(exception)}")
