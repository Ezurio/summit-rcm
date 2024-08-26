#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""Service Module to handle provisioning"""

import asyncio
from datetime import datetime
import os
from enum import IntEnum
from syslog import LOG_ERR, syslog
import shutil
from pathlib import Path
from typing import Optional, Tuple

try:
    from dbus_fast import Message, MessageType
    from summit_rcm.dbus_manager import DBusManager
except ImportError as error:
    # Ignore the error if the dbus_fast module is not available if generating documentation
    if os.environ.get("DOCS_GENERATION") != "True":
        raise error
import falcon.asgi.multipart
from summit_rcm.settings import ServerConfig
from summit_rcm.definition import (
    DEVICE_CA_CERT_CHAIN_PATH,
    DEVICE_SERVER_KEY_PATH,
    DEVICE_SERVER_CSR_PATH,
    DEVICE_SERVER_CERT_PATH,
    PROVISIONING_DIR,
    PROVISIONING_CA_CERT_CHAIN_PATH,
    PROVISIONING_STATE_FILE_PATH,
    CERT_TEMP_PATH,
    CONFIG_FILE_TEMP_PATH,
    SYSTEMD_BUS_NAME,
    SYSTEMD_MAIN_OBJ,
    SYSTEMD_MANAGER_IFACE,
)

try:
    import openssl_extension
except ImportError as error:
    # Ignore the error if the openssl_extension module is not available if generating documentation
    if os.environ.get("DOCS_GENERATION") != "True":
        raise error


OPENSSL_CERT_DATETIME_FORMAT = "%b %d %H:%M:%S %Y %Z"
TOUCH_TIMESTAMP_FORMAT = "%Y%m%d%H%M.%S"
FALLBACK_TIMESTAMP_FILE_PATH = "/etc/fallback_timestamp"
CLIENT_CERT_TEMP_PATH = "/tmp/client.crt"


class ProvisioningState(IntEnum):
    """Enumeration of provisioning states"""

    UNPROVISIONED = 0
    """No provisioning has been completed"""

    PARTIALLY_PROVISIONED = 1
    """The device key/certificate has been provisioned, but the initial time has not been set"""

    FULLY_PROVISIONED = 2
    """The device has been fully provisioned"""


class CertificateProvisioningService:
    """
    Manage device server key/certificate provisioning
    """

    @staticmethod
    def parse_datetime_from_openssl_str(datetime_str: str) -> datetime:
        """Parse the given OpenSSL format date/time string into a datetime object"""
        if datetime_str is None:
            raise Exception()

        return datetime.strptime(datetime_str, OPENSSL_CERT_DATETIME_FORMAT)

    @staticmethod
    def get_client_cert_validity_period(
        req: falcon.asgi.Request,
    ) -> Tuple[datetime, datetime]:
        """
        Retrieve the validity period from the client's certificate using the falcon.request.scope
        """
        if (
            not req.scope.get("extensions", None)
            or not req.scope["extensions"].get("tls", None)
            or req.scope["extensions"]["tls"].get("client_cert_error", None)
            or len(req.scope["extensions"]["tls"].get("client_cert_chain", [])) == 0
        ):
            raise Exception("Could not read client certificate validity period")

        with open(CLIENT_CERT_TEMP_PATH, "wb") as client_cert:
            client_cert.write(
                str(req.scope["extensions"]["tls"]["client_cert_chain"][0]).encode(
                    "utf-8"
                )
            )

        cert_info = openssl_extension.get_cert_info(CLIENT_CERT_TEMP_PATH, "")
        Path(CLIENT_CERT_TEMP_PATH).unlink(missing_ok=True)

        return (
            CertificateProvisioningService.parse_datetime_from_openssl_str(
                cert_info.get("not_before", None)
            ),
            CertificateProvisioningService.parse_datetime_from_openssl_str(
                cert_info.get("not_after", None)
            ),
        )

    @staticmethod
    def get_client_cert_hash(req: falcon.asgi.Request) -> int:
        """
        Retrieve the hash of the client's certificate using the falcon.request.scope
        """
        if (
            not req.scope.get("extensions", None)
            or not req.scope["extensions"].get("tls", None)
            or req.scope["extensions"]["tls"].get("client_cert_error", None)
            or len(req.scope["extensions"]["tls"].get("client_cert_chain", [])) == 0
        ):
            raise Exception("Could not read client certificate hash")

        return hash(req.scope["extensions"]["tls"]["client_cert_chain"][0])

    @staticmethod
    def get_ca_cert_validity_period() -> Tuple[datetime, datetime]:
        """
        Retrieve the validity period from the CA certificate using OpenSSL.
        """
        ca_cert_path = (
            ServerConfig()
            .get_parser()
            .get(
                section="global",
                option="server.ssl_certificate_chain",
                fallback=DEVICE_CA_CERT_CHAIN_PATH,
            )
            .strip('"')
        )

        if not Path(ca_cert_path).exists():
            raise Exception(
                "Could not get CA certificate validity period - file not found"
            )

        cert_info = openssl_extension.get_cert_info(ca_cert_path, "")

        return (
            CertificateProvisioningService.parse_datetime_from_openssl_str(
                cert_info.get("not_before", None)
            ),
            CertificateProvisioningService.parse_datetime_from_openssl_str(
                cert_info.get("not_after", None)
            ),
        )

    @staticmethod
    def get_validity_period(req: falcon.asgi.Request) -> Tuple[datetime, datetime]:
        """
        Determine the current valid timestamps for setting the current time first using the client's
        certificate validity period, and if that isn't present,
        using the CA certificate's validity period.
        """
        try:
            return CertificateProvisioningService.get_client_cert_validity_period(req)
        except Exception:
            # Couldn't read the validity period from the client certificate, so just continue
            pass

        try:
            return CertificateProvisioningService.get_ca_cert_validity_period()
        except Exception:
            # Couldn't read the validity period from the CA certificate, so throw an exception
            raise Exception("Could not get validity period")

    @staticmethod
    def validate_new_timestamp(
        new_timestamp_usec: int, req: falcon.asgi.Request
    ) -> bool:
        """
        Validate the given timestamp against the current validity period.
        """

        try:
            new_timestamp_dt = datetime.fromtimestamp(new_timestamp_usec / 1000000)
            not_before, not_after = CertificateProvisioningService.get_validity_period(
                req
            )
            return new_timestamp_dt > not_before and new_timestamp_dt < not_after
        except Exception as exception:
            syslog(f"Could not validate timestamp - {str(exception)}")
            return False

    @staticmethod
    def get_provisioning_state() -> ProvisioningState:
        """Read current provisioning state"""

        if not Path(PROVISIONING_STATE_FILE_PATH).exists():
            CertificateProvisioningService.set_provisioning_state(
                ProvisioningState.UNPROVISIONED
            )
            return ProvisioningState.UNPROVISIONED

        try:
            with open(PROVISIONING_STATE_FILE_PATH, "r") as provisioning_state_file:
                return ProvisioningState(int(provisioning_state_file.read()))
        except Exception as exception:
            syslog(f"Unable to read provisioning state - {str(exception)}")
            return ProvisioningState.UNPROVISIONED

    @staticmethod
    def set_provisioning_state(provisioning_state: ProvisioningState):
        """Update the provisioning state file on disk"""
        Path(PROVISIONING_DIR).mkdir(exist_ok=True)
        with open(PROVISIONING_STATE_FILE_PATH, "w") as provisioning_state_file:
            provisioning_state_file.write(str(int(provisioning_state)))

    @staticmethod
    async def generate_key_and_csr(
        openssl_key_gen_args: Optional[str] = None,
    ):
        """
        Utilize OpenSSL to generate a private key and CSR using the provided configuration file. If
        desired, optional OpenSSL key generation args can be provided.
        """
        if not Path(CONFIG_FILE_TEMP_PATH).exists():
            raise Exception("Config file not found")

        Path(PROVISIONING_DIR).mkdir(exist_ok=True)

        if Path(DEVICE_SERVER_KEY_PATH).exists():
            # Private key has already been generated, remove it
            Path(DEVICE_SERVER_KEY_PATH).unlink()

        if openssl_key_gen_args:
            # Generate the key using the arguments provided
            args = ["openssl"]
            args.extend(openssl_key_gen_args.split(" "))
            proc = await asyncio.create_subprocess_exec(
                *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await proc.communicate()
            if proc.returncode:
                raise Exception(stderr.decode("utf-8"))

            if not Path(DEVICE_SERVER_KEY_PATH).exists():
                raise Exception("Key file not found")

            # Build the args to use the new key
            args = [
                "openssl",
                "req",
                "-new",
                "-key",
                DEVICE_SERVER_KEY_PATH,
                "-out",
                DEVICE_SERVER_CSR_PATH,
                "-config",
                CONFIG_FILE_TEMP_PATH,
            ]
        else:
            # Build the args to generate a key and CSR using the default algorithm (ECDSA with the
            # prime256v1 curve
            args = [
                "openssl",
                "req",
                "-nodes",
                "-newkey",
                "ec",
                "-pkeyopt",
                "ec_paramgen_curve:prime256v1",
                "-pkeyopt",
                "ec_param_enc:named_curve",
                "-keyout",
                DEVICE_SERVER_KEY_PATH,
                "-out",
                DEVICE_SERVER_CSR_PATH,
                "-config",
                CONFIG_FILE_TEMP_PATH,
            ]

        proc = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        if proc.returncode:
            raise Exception(stderr.decode("utf-8"))

    @staticmethod
    async def verify_certificate_against_ca(cert_path: str, ca_cert_path: str) -> bool:
        """Utilize OpenSSL to verify a certificate against a CA certificate"""
        try:
            proc = await asyncio.create_subprocess_exec(
                *["openssl", "verify", "-CAfile", ca_cert_path, cert_path],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()

            if proc.returncode:
                raise Exception(stderr.decode("utf-8"))

            return True
        except Exception as exception:
            syslog(LOG_ERR, f"Error verifying certificate: {str(exception)}")
            return False

    @staticmethod
    async def save_certificate_file():
        """
        Save an incoming certificate file as the device's server certificate after verifying it
        against the provisioning CA certificate chain
        """
        if not Path(CERT_TEMP_PATH).exists():
            raise Exception("Certificate file not found")

        # Verify the certificate
        if not await CertificateProvisioningService.verify_certificate_against_ca(
            CERT_TEMP_PATH, PROVISIONING_CA_CERT_CHAIN_PATH
        ):
            raise InvalidCertificateError()

        # Move the certificate to the target path
        Path(PROVISIONING_DIR).mkdir(exist_ok=True)
        shutil.move(CERT_TEMP_PATH, DEVICE_SERVER_CERT_PATH)

        # Flag that the device is now partially provisioned
        CertificateProvisioningService.set_provisioning_state(
            ProvisioningState.PARTIALLY_PROVISIONED
        )

    @staticmethod
    def read_fallback_timestamp() -> Optional[datetime]:
        """Read the fallback timestamp from the fallback timestamp file"""
        try:
            fallback_timestamp_file = Path(FALLBACK_TIMESTAMP_FILE_PATH)

            return (
                datetime.fromtimestamp(fallback_timestamp_file.stat().st_mtime)
                if fallback_timestamp_file.exists()
                else None
            )
        except Exception as exception:
            syslog(LOG_ERR, f"Error reading fallback timestamp - {str(exception)}")
            return None

    @staticmethod
    def set_fallback_timestamp(fallback_timestamp: datetime):
        """Set the fallback timestamp file to the given datetime"""
        try:
            fallback_timestamp_file = Path(FALLBACK_TIMESTAMP_FILE_PATH)

            if not fallback_timestamp_file.exists():
                fallback_timestamp_file.touch()

            # Call os.utime() to update the timestamp on the fallback timestamp file which accepts a
            # tuple of (access_time, modification_time)
            os.utime(
                path=fallback_timestamp_file,
                times=(
                    fallback_timestamp_file.stat().st_atime,
                    fallback_timestamp.timestamp(),
                ),
            )
        except Exception as exception:
            syslog(LOG_ERR, f"Error setting fallback timestamp: {str(exception)}")

    @staticmethod
    async def restart_summit_rcm() -> bool:
        """Restart the summit-rcm systemd service via D-Bus"""
        try:
            bus = await DBusManager().get_bus()

            reply = await bus.call(
                Message(
                    destination=SYSTEMD_BUS_NAME,
                    path=SYSTEMD_MAIN_OBJ,
                    interface=SYSTEMD_MANAGER_IFACE,
                    member="RestartUnit",
                    signature="ss",
                    body=["summit-rcm.service", "replace"],
                )
            )

            if reply.message_type == MessageType.ERROR:
                raise Exception()

            return True
        except Exception as exception:
            syslog(LOG_ERR, f"Could not restart summit-rcm: {str(exception)}")
            return False


class InvalidCertificateError(Exception):
    """
    Custom error class for when the provided certificate cannot be verified against the provisioning
    CA certificate chain
    """
