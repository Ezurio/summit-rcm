import json
import os
from subprocess import run
from syslog import syslog, LOG_ERR
from typing import List, Tuple
import falcon
from ..definition import SUMMIT_RCM_ERRORS

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
FIREWALL_GET_MAX_PATH_DEPTH = 2
FIREWALL_PUT_MAX_PATH_DEPTH = 3


class Firewall:
    """
    iptables-based wrapper to support basic firewall control (i.e., port forwarding)
    """

    def __init__(self):
        self.load_forwarded_ports()

    def load_forwarded_ports(self) -> None:
        """
        Load the list of forwarded ports from disk
        """
        try:
            if os.path.exists(FORWARDED_PORTS_FILE):
                with open(FORWARDED_PORTS_FILE, "r") as forwarded_ports_file:
                    self.forwarded_ports = json.loads(forwarded_ports_file.read())
            else:
                self.forwarded_ports = []
        except Exception as e:
            self.log_exception(e, "Unable to load forwarded ports")
            self.forwarded_ports = []

    def save_forwarded_ports(self) -> None:
        """
        Save the list of forwarded ports to disk
        """
        try:
            with open(FORWARDED_PORTS_FILE, "w") as forwarded_ports_file:
                forwarded_ports_file.write(json.dumps(self.forwarded_ports))
        except Exception as e:
            self.log_exception(e, "Unable to save forwarded ports")

    def log_exception(self, e, message: str = "") -> None:
        """
        Log an exception
        """
        syslog(LOG_ERR, message + str(e))

    def check_parameters(self, post_data, parameters: List[str]):
        """
        Verify required parameters are present in the provided post data. If not, raise a ValueError
        exception.
        """
        for parameter in parameters:
            if parameter not in post_data:
                raise ValueError(f"required parameter '{parameter}' not specified")

    def configure_forwarded_port(
        self,
        command: str,
        port: str,
        protocol: str,
        toport: str,
        toaddr: str,
        ip_version: str = IPV4,
    ) -> Tuple[bool, str]:
        """
        Add/remove forwarded port.

        Return value is a tuple in the form of: (success, message)
        """
        # Check if a forwarded port is already present with the given parameters and exit early if
        # appropriate.
        forwarded_port_present: bool = False
        for forwarded_port in self.forwarded_ports:
            if (
                forwarded_port["port"] == port
                and forwarded_port["protocol"] == protocol
                and forwarded_port["toport"] == toport
                and forwarded_port["toaddr"] == toaddr
                and forwarded_port["ip_version"] == ip_version
            ):
                forwarded_port_present = True
                break
        if command == ADD_PORT and forwarded_port_present:
            return (True, "Forwarded port already exists")
        elif command == REMOVE_PORT and not forwarded_port_present:
            return (False, "Forwarded port doesn't exist")

        # Add/remove PREROUTING rule
        proc = run(
            [
                IPTABLES if ip_version == IPV4 else IP6TABLES,
                "-t",
                "nat",
                "-A" if command == ADD_PORT else "-D",
                "PREROUTING",
                "-p",
                protocol,
                "-i",
                WIFI_INTERFACE,
                "--dport",
                port,
                "-j",
                "DNAT",
                "--to-destination",
                f"{toaddr}:{toport}" if ip_version == IPV4 else f"[{toaddr}]:{toport}",
            ],
            capture_output=True,
        )
        if proc.returncode != 0:
            msg = "Error %s forwarded port: %s" % (
                "adding" if command == ADD_PORT else "removing",
                proc.stderr.decode("utf-8").strip(),
            )
            syslog(LOG_ERR, msg)
            return (False, msg)

        # Add/remove FORWARD rule
        proc = run(
            [
                IPTABLES if ip_version == IPV4 else IP6TABLES,
                "-A" if command == ADD_PORT else "-D",
                "FORWARD",
                "-p",
                protocol,
                "-d",
                toaddr,
                "--dport",
                toport,
                "-m",
                "state",
                "--state",
                "NEW",
                "-j",
                "ACCEPT",
            ],
            capture_output=True,
        )
        if proc.returncode != 0:
            msg = "Error %s forwarded port: %s" % (
                "adding" if command == ADD_PORT else "removing",
                proc.stderr.decode("utf-8").strip(),
            )
            syslog(LOG_ERR, msg)
            return (False, msg)

        # Update stored list of forwarded ports
        if command == ADD_PORT:
            self.forwarded_ports.append(
                {
                    "port": port,
                    "protocol": protocol,
                    "toport": toport,
                    "toaddr": toaddr,
                    "ip_version": ip_version,
                }
            )
        else:
            self.forwarded_ports[:] = [
                x
                for x in self.forwarded_ports
                if not (
                    x["port"] == port
                    and x["protocol"] == protocol
                    and x["toport"] == toport
                    and x["toaddr"] == toaddr
                    and x["ip_version"] == ip_version
                )
            ]
        self.save_forwarded_ports()

        return (True, "")

    @staticmethod
    def open_port(port: str, ip_version: str = IPV4V6):
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
                proc = run(
                    [
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
                    capture_output=True,
                )
                if proc.returncode != 0:
                    msg = "Error opening port %s: %s" % (
                        port,
                        proc.stderr.decode("utf-8").strip(),
                    )
                    syslog(LOG_ERR, msg)
                    return
        except Exception as e:
            syslog(LOG_ERR, f"Unable to open firewall port: {str(e)}")

    @staticmethod
    def close_port(port: str, ip_version: str = IPV4V6):
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
                proc = run(
                    [
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
                    capture_output=True,
                )
                if proc.returncode != 0:
                    msg = "Error closing port %s: %s" % (
                        port,
                        proc.stderr.decode("utf-8").strip(),
                    )
                    syslog(LOG_ERR, msg)
                    return
        except Exception as e:
            syslog(LOG_ERR, f"Unable to close firewall port: {str(e)}")

    @staticmethod
    def result_parameter_not_one_of(parameter: str, supplied_value: str, not_one_of):
        """
        Generate return object value for when a supplied value is not valid
        """
        return {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": f"supplied parameter '{parameter}' value {supplied_value} must be one of"
            f" {not_one_of}, ",
        }

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "",
        }

        try:
            result["Forward"] = self.forwarded_ports
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as e:
            self.log_exception(e)
            result["InfoMsg"] = f"Error: {str(e)}"
        resp.media = result

    async def on_put(self, req, resp, command):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "",
        }

        try:
            post_data = await req.get_media()

            if command:
                if command not in PORT_COMMANDS:
                    result.update(
                        self.result_parameter_not_one_of(
                            "command", command, PORT_COMMANDS
                        )
                    )
                else:
                    self.check_parameters(
                        post_data, ["port", "protocol", "toport", "toaddr"]
                    )
                    port = post_data["port"]
                    protocol = post_data["protocol"]
                    toport = post_data["toport"]
                    toaddr = post_data["toaddr"]
                    ip_version = post_data.get("ip_version", None)
                    if ip_version and ip_version not in IP_VERSIONS:
                        result.update(
                            self.result_parameter_not_one_of(
                                "ip_version", ip_version, IP_VERSIONS
                            )
                        )
                        resp.media = result
                        return
                    success, msg = self.configure_forwarded_port(
                        command,
                        port,
                        protocol,
                        toport,
                        toaddr,
                        ip_version if ip_version else IPV4,
                    )
                    result["InfoMsg"] = msg
                    if success:
                        result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            else:
                result["InfoMsg"] = "No command specified"
        except Exception as e:
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
            self.log_exception(e)
            result["InfoMsg"] = f"Error: {str(e)}"

        resp.media = result
