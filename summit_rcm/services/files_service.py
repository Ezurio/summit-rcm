#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to interact with files.
"""

import asyncio
import configparser
import os
import shlex
from shutil import copy2, rmtree
from subprocess import run
from syslog import LOG_ERR, syslog
from typing import Any, List, Tuple
from pathlib import Path

try:
    import aiofiles
except ImportError as error:
    # Ignore the error if the aiofiles module is not available if generating documentation
    if os.environ.get("DOCS_GENERATION") != "True":
        raise error
from summit_rcm import definition
from summit_rcm.services.network_service import (
    ConnectionProfileReservedError,
    NetworkService,
)
from summit_rcm.settings import ServerConfig, SystemSettingsManage
from summit_rcm.utils import Singleton
from summit_rcm.services.network_manager_service import NetworkManagerService
from summit_rcm.services.system_service import FACTORY_RESET_SCRIPT

CONNECTION_TMP_ARCHIVE_FILE = "/tmp/archive.zip"
CONFIG_TMP_ARCHIVE_FILE = "/tmp/config.zip"
LOG_TMP_ARCHIVE_FILE = "/tmp/log.zip"
DEBUG_TMP_ARCHIVE_FILE = "/tmp/debug.zip"
TMP_TMP_ARCHIVE_FILE = "/tmp/tmp.zip"
TMP_ARCHIVE_DIRECTORY = "/tmp/import"
FILE_READ_SIZE = 8192
UNZIP = "/usr/bin/unzip"
ZIP = "/usr/bin/zip"
NETWORKMANAGER_DIR = "etc/NetworkManager"
NETWORKMANAGER_DIR_FULL = "/etc/NetworkManager/"
DATA_SECRET_NETWORKMANAGER_DIR = "/data/secret/NetworkManager"
SECURED_FWUPDATE_FILE_PATH = "/data/summit-rcm-update.swu"
UNSECURED_FWUPDATE_FILE_PATH = "/usr/share/summit-rcm-update.swu"
PERSISTENT_LOG_PATH = "/var/log/journal/"
VOLATILE_LOG_PATH = "/run/log/journal/"


class FilesService(metaclass=Singleton):
    """
    Service to interact with files.
    """

    @staticmethod
    def get_log_path() -> str:
        """Retrieve the path to where system logs are stored"""
        # Log will be saved in "/run/log/journal/" for volatile mode  or "/var/log/journal/" for
        # persistent mode. If "/var/log/journal/" exists and "/run/log/journal" is non-empty, the
        # journal should be operating in volatile mode.
        # https://www.freedesktop.org/software/systemd/man/journald.conf.html#Storage=
        if not os.path.exists(PERSISTENT_LOG_PATH) or (
            os.path.exists(VOLATILE_LOG_PATH) and len(os.listdir(VOLATILE_LOG_PATH)) > 0
        ):
            return VOLATILE_LOG_PATH

        return PERSISTENT_LOG_PATH

    @staticmethod
    def get_fwupdate_file_path() -> str:
        """Retrieve the path to where the firmware update file is stored"""
        # For secured SD card builds, the /data path is present and writeable, so we can use it to
        # temporarily store the .swu file. For unsecured builds, the whole rootfs is writeable, so
        # we can use /usr/share to temporarily store the .swu file.
        return (
            SECURED_FWUPDATE_FILE_PATH
            if os.path.exists("/data")
            else UNSECURED_FWUPDATE_FILE_PATH
        )

    @staticmethod
    async def handle_file_upload_bytes(data: bytes, path: str, mode: str = "wb") -> str:
        """
        Handle file upload as bytes
        """
        with open(path, mode) as dest:
            dest.write(data)
        return path

    @staticmethod
    async def handle_file_download(path: str):
        """
        Handle when a client downloads a file
        """
        if not Path(path).exists():
            raise Exception("File not found")

        return await aiofiles.open(path, "rb")

    @staticmethod
    async def handle_cert_file_upload_bytes(
        incoming_data: bytes,
        name: str,
        mode: str = "wb",
    ):
        """
        Handle when a client uploads a certificate file
        """
        return await FilesService.handle_file_upload_bytes(
            incoming_data, str(Path(NETWORKMANAGER_DIR_FULL, "certs", name)), mode
        )

    @staticmethod
    async def handle_connection_import_file_upload_bytes(
        incoming_data: bytes, mode: str = "wb"
    ):
        """
        Handle when a client uploads an archive for importing connections
        """
        return await FilesService.handle_file_upload_bytes(
            incoming_data, CONNECTION_TMP_ARCHIVE_FILE, mode
        )

    @staticmethod
    async def handle_config_import_file_upload_bytes(
        incoming_data: bytes, mode: str = "wb"
    ):
        """
        Handle when a client uploads an archive for importing system configuration
        """
        return await FilesService.handle_file_upload_bytes(
            incoming_data, CONFIG_TMP_ARCHIVE_FILE, mode
        )

    @staticmethod
    async def handle_ssl_file_upload_bytes(
        incoming_data: bytes, name: str, mode: str = "wb"
    ):
        """
        Handle when a client uploads an SSL file
        """
        ssl_dir = f"{ServerConfig().data_dir}/client-ssl/"
        ssl_file_path = Path(ssl_dir)
        ssl_file_path.mkdir(parents=True, exist_ok=True)
        return await FilesService.handle_file_upload_bytes(
            incoming_data, str(Path(ssl_dir, name)), mode
        )

    @staticmethod
    async def handle_swupdate_file_upload_bytes(incoming_data: bytes, mode: str = "wb"):
        """
        Handle when a client uploads a software update file
        """
        return await FilesService.handle_file_upload_bytes(
            incoming_data, FilesService.get_fwupdate_file_path(), mode
        )

    @staticmethod
    def is_encrypted_storage_toolkit_enabled() -> bool:
        """
        Determines whether or not the Summit Encrypted Storage Toolkit is enabled on the running
        image.
        """
        return Path(FACTORY_RESET_SCRIPT).exists()

    @staticmethod
    async def import_connections(
        password: str, overwrite_existing: bool
    ) -> Tuple[bool, str]:
        """
        Handle importing NetworkManager connections and certificates from a properly structured and
        encrypted zip archive overwriting existing connections, if specified

        Return value is a tuple in the form of: (success, message)
        """
        if not Path(CONNECTION_TMP_ARCHIVE_FILE).exists():
            return (False, "Invalid archive")

        result = (False, "Unknown error")
        try:
            # Extract the archive using 'unzip' (the built-in Python zipfile implementation is
            # handled in pure Python, is "extremely slow", and does not support generating
            # encrypted archives).
            # https://docs.python.org/3/library/zipfile.html
            proc = run(
                [
                    UNZIP,
                    "-P",
                    password,
                    "-n",
                    CONNECTION_TMP_ARCHIVE_FILE,
                    "-d",
                    TMP_ARCHIVE_DIRECTORY,
                ],
                capture_output=True,
            )
            if proc.returncode != 0:
                raise Exception(proc.stderr.decode("utf-8"))

            # Verify expected sub directories ('system-connections' and 'certs') are present
            if (
                not Path(
                    TMP_ARCHIVE_DIRECTORY, NETWORKMANAGER_DIR, "system-connections"
                ).exists()
                or not Path(TMP_ARCHIVE_DIRECTORY, NETWORKMANAGER_DIR, "certs").exists()
            ):
                raise Exception("Expected files missing")

            # Copy connections
            for file in Path(
                TMP_ARCHIVE_DIRECTORY, NETWORKMANAGER_DIR, "system-connections"
            ).iterdir():
                try:
                    # Check for reserved connections
                    if FilesService.imported_connection_is_reserved(file):
                        raise ConnectionProfileReservedError("Reserved")

                    # Check for existing connections
                    if (
                        not overwrite_existing
                        and await FilesService.imported_connection_exists(file)
                    ):
                        raise Exception("Connection exists")

                    dest = Path(
                        "/", NETWORKMANAGER_DIR, "system-connections", file.name
                    )
                    if dest.is_symlink():
                        raise Exception("Symlink")

                    copy2(
                        file,
                        dest,
                        follow_symlinks=False,
                    )
                except Exception as exception:
                    syslog(
                        LOG_ERR,
                        f"Could not import connection file {str(file)} - {str(exception)}",
                    )

            # Copy certs
            for file in Path(
                TMP_ARCHIVE_DIRECTORY, NETWORKMANAGER_DIR, "certs"
            ).iterdir():
                try:
                    dest = Path("/", NETWORKMANAGER_DIR, "certs", file.name)
                    if dest.is_symlink():
                        raise Exception("Symlink")

                    copy2(
                        file,
                        dest,
                        follow_symlinks=False,
                    )
                except Exception as exception:
                    syslog(
                        LOG_ERR,
                        f"Could not import certificate file {str(file)} - {str(exception)}",
                    )

            # Request NetworkManager to reload connections
            if not await NetworkManagerService().reload_connections():
                return (False, "Unable to reload connections after import")

            result = (True, "")
        except Exception as exception:
            result = (False, str(exception))
        finally:
            # Delete the temp file if present
            Path(CONNECTION_TMP_ARCHIVE_FILE).unlink(missing_ok=True)

            # Delete the temp dir if present
            try:
                rmtree(TMP_ARCHIVE_DIRECTORY, ignore_errors=True)
            except Exception as exception:
                msg = f"Error cleaning up connection imports: {str(exception)}"
                result = (False, msg)

        return result

    @staticmethod
    def export_connections(password: str) -> Tuple[bool, str, Any]:
        """
        Handle exporting NetworkManager connections and certificates as a properly structured and
        encrypted zip archive

        Return value is a tuple in the form of: (success, message, archive_path)
        """
        result = (False, "Unknown error", None)
        try:
            # Generate the archive using 'zip' (the built-in Python zipfile implementation is
            # handled in pure Python, is "extremely slow", and does not support generating
            # encrypted archives).
            # https://docs.python.org/3/library/zipfile.html
            proc = run(
                [
                    ZIP,
                    "-P",
                    password,
                    "-9",
                    "-r",
                    CONNECTION_TMP_ARCHIVE_FILE,
                    str(Path("/", NETWORKMANAGER_DIR, "system-connections")),
                    str(Path("/", NETWORKMANAGER_DIR, "certs")),
                ],
                capture_output=True,
            )
            if proc.returncode != 0:
                raise Exception(proc.stderr.decode("utf-8"))

            if not Path(CONNECTION_TMP_ARCHIVE_FILE).exists():
                raise Exception("archive generation failed")

            return (True, "", CONNECTION_TMP_ARCHIVE_FILE)
        except Exception as exception:
            msg = f"Unable to export connections - {str(exception)}"
            syslog(LOG_ERR, msg)
            result = (False, msg, None)
        return result

    @staticmethod
    def get_files_by_type(file_type: str) -> List[str]:
        """Retrieve a list of files of the specified type ('cert' or 'pac')"""
        if file_type not in ["cert", "pac"]:
            return []

        files = []
        for entry in Path(definition.FILEDIR_DICT.get(file_type)).iterdir():
            if entry.exists() and entry.suffix in definition.FILEFMT_DICT.get(
                file_type
            ):
                files.append(entry.name)
        files.sort()
        return files

    @staticmethod
    def get_cert_files() -> List[str]:
        """Retrieve a list of certificate files"""
        return FilesService.get_files_by_type("cert")

    @staticmethod
    def get_pac_files() -> List[str]:
        """Retrieve a list of PAC files"""
        return FilesService.get_files_by_type("pac")

    @staticmethod
    def get_cert_and_pac_files() -> List[str]:
        """Retrieve a list of all certificate and PAC files"""
        files = FilesService.get_cert_files() + FilesService.get_pac_files()
        files.sort()
        return files

    @staticmethod
    def delete_cert_file(name: str):
        """Delete the specified file if present"""
        name = Path(name).name
        path = Path(NETWORKMANAGER_DIR_FULL, "certs", name)
        if not path.exists():
            raise FileNotFoundError()

        path.unlink()

    @staticmethod
    def get_other_config_files() -> List[str]:
        """
        Retrieve a list of other config files that should be included in config exports/imports
        """
        other_config_files = []
        directories = ["/etc/chrony", "/etc/dropbear", "/etc/stunnel"]
        for directory in directories:
            if Path(directory).exists():
                other_config_files.append(f"{directory}/*")

        return other_config_files

    @staticmethod
    def get_timezone_file_paths() -> List[str]:
        """
        Retrieve the file paths for timezone related files that should be included in config
        exports/imports. When the encrypted storage toolkit is enabled, /etc/localtime is a symlink
        to a file in /data, so it will be included as part of the config export/import. When the
        encrypted storage toolkit is not enabled, /etc/localtime is a regular file that should be
        included in the config export/import. /etc/adjtime and /etc/timezone may also be present and
        should be included if they are.
        """
        timezone_files = []

        localtime_path = Path("/etc/localtime")
        if localtime_path.is_symlink():
            timezone_files.append(str(localtime_path.readlink()))
        elif localtime_path.exists():
            timezone_files.append("/etc/localtime")

        adjtime_path = Path("/etc/adjtime")
        if adjtime_path.is_symlink():
            timezone_files.append(str(adjtime_path.readlink()))
        elif adjtime_path.exists():
            timezone_files.append("/etc/adjtime")

        timezone_path = Path("/etc/timezone")
        if timezone_path.is_symlink():
            timezone_files.append(str(timezone_path.readlink()))
        elif timezone_path.exists():
            timezone_files.append("/etc/timezone")

        return timezone_files

    @staticmethod
    async def export_system_config(password: str) -> Tuple[bool, str, Any]:
        """
        Handle exporting Summit RCM system configuration as a properly structured and encrypted zip
        archive.

        Return value is a tuple in the form of: (success, message, archive_path)
        """
        result = (False, "Unknown error", None)
        try:
            # Generate the archive using 'zip' (the built-in Python zipfile implementation is
            # handled in pure Python, is "extremely slow", and does not support generating
            # encrypted archives).
            # https://docs.python.org/3/library/zipfile.html
            proc = await asyncio.create_subprocess_shell(
                f"cd / && {ZIP} --symlinks --password {password} -9 -r {CONFIG_TMP_ARCHIVE_FILE} "
                f"{shlex.quote(ServerConfig().settings_file)} "
                "/etc/NetworkManager/certs/* "
                "/etc/NetworkManager/system-connections/* "
                f"{' '.join(FilesService.get_timezone_file_paths())} "
                f"{' '.join(FilesService.get_other_config_files())}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise Exception(
                    f"err: {stderr.decode('utf-8')}, "
                    f"out: {stdout.decode('utf-8')}, "
                    f"returncode: {proc.returncode}"
                )

            if not Path(CONFIG_TMP_ARCHIVE_FILE).exists():
                raise Exception("archive generation failed")

            return (True, "", CONFIG_TMP_ARCHIVE_FILE)
        except Exception as exception:
            msg = f"Unable to export system config - {str(exception)}"
            result = (False, msg, None)
        return result

    @staticmethod
    async def import_system_config(password: str) -> Tuple[bool, str]:
        """
        Handle importing Summit RCM system config from a properly structured and encrypted zip
        archive.

        Return value is a tuple in the form of: (success, message)
        """
        if not Path(CONFIG_TMP_ARCHIVE_FILE).exists():
            return (False, "Invalid archive")

        result = (False, "Unknown error")
        try:
            # Test that the file is encrypted
            proc = await asyncio.create_subprocess_shell(
                f"cd / && {UNZIP} -P 1234 -t {CONFIG_TMP_ARCHIVE_FILE}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                raise Exception(
                    "archive not encrypted - "
                    f"err: {stderr.decode('utf-8')}, "
                    f"out: {stdout.decode('utf-8')}, "
                    f"returncode: {proc.returncode}"
                )

            # Test that the password is correct
            proc = await asyncio.create_subprocess_shell(
                f"cd / && {UNZIP} -P {password} -t {CONFIG_TMP_ARCHIVE_FILE}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise Exception(
                    "incorrect password - "
                    f"err: {stderr.decode('utf-8')}, "
                    f"out: {stdout.decode('utf-8')}, "
                    f"returncode: {proc.returncode}"
                )

            # Remove current config settings
            proc = await asyncio.create_subprocess_shell(
                f"cd / && rm -fr /etc/NetworkManager/system-connections/* "
                "/etc/NetworkManager/certs/* "
                f"{shlex.quote(ServerConfig().settings_file)} "
                f"{' '.join(FilesService.get_timezone_file_paths())} "
                f"{' '.join(FilesService.get_other_config_files())}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise Exception(
                    "Could not remove current config settings - "
                    f"err: {stderr.decode('utf-8')}, "
                    f"out: {stdout.decode('utf-8')}, "
                    f"returncode: {proc.returncode}"
                )

            # Extract the archive using 'unzip' (the built-in Python zipfile implementation is
            # handled in pure Python, is "extremely slow", and does not support generating
            # encrypted archives).
            # https://docs.python.org/3/library/zipfile.html
            proc = await asyncio.create_subprocess_shell(
                f"cd / && {UNZIP} -P {password} -o {CONFIG_TMP_ARCHIVE_FILE}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise Exception(
                    f"err: {stderr.decode('utf-8')}, "
                    f"out: {stdout.decode('utf-8')}, "
                    f"returncode: {proc.returncode}"
                )

            # Requst NetworkManager to reload connections
            if not await NetworkManagerService().reload_connections():
                return (False, "Unable to reload connections after import")

            result = (True, "")
        except Exception as exception:
            result = (False, str(exception))
        finally:
            # Delete the temp file if present
            Path(CONFIG_TMP_ARCHIVE_FILE).unlink(missing_ok=True)

        return result

    @staticmethod
    def export_logs(password: str) -> Tuple[bool, str, Any]:
        """
        Handle exporting logs as a properly structured and encrypted zip archive.

        Return value is a tuple in the form of: (success, message, archive_path)
        """
        result = (False, "Unknown error", None)

        try:
            # Generate the archive using 'zip' (the built-in Python zipfile implementation is
            # handled in pure Python, is "extremely slow", and does not support generating
            # encrypted archives).
            # https://docs.python.org/3/library/zipfile.html
            proc = run(
                [
                    ZIP,
                    "--symlinks",
                    "-P",
                    password,
                    "-9",
                    "-r",
                    LOG_TMP_ARCHIVE_FILE,
                    ".",
                ],
                cwd=FilesService.get_log_path(),
                capture_output=True,
            )
            if proc.returncode != 0:
                raise Exception(proc.stdout.decode("utf-8"))

            if not Path(LOG_TMP_ARCHIVE_FILE).exists():
                raise Exception("archive generation failed")

            return (True, "", LOG_TMP_ARCHIVE_FILE)
        except Exception as exception:
            msg = f"Unable to export logs - {str(exception)}"
            result = (False, msg, None)
        return result

    @staticmethod
    def export_debug() -> Tuple[bool, str, Any]:
        """
        Handle exporting logs and system configuration as a properly structured and encrypted zip
        archive using OpenSSL encryption.

        Return value is a tuple in the form of: (success, message, archive_path)
        """
        result = (False, "Unknown error", None)

        try:
            debug_paths: list[str] = [
                FilesService.get_log_path(),
                NETWORKMANAGER_DIR_FULL,
                f"{ServerConfig().data_dir}/",
            ]

            # Generate the archive using 'zip' (the built-in Python zipfile implementation is
            # handled in pure Python, is "extremely slow", and does not support generating
            # encrypted archives).
            # https://docs.python.org/3/library/zipfile.html
            proc = run(
                [
                    ZIP,
                    "-9",
                    "-r",
                    TMP_TMP_ARCHIVE_FILE,
                ]
                + debug_paths,
                capture_output=True,
            )
            if proc.returncode != 0:
                raise Exception(proc.stderr.decode("utf-8"))

            if not Path(TMP_TMP_ARCHIVE_FILE).exists():
                raise Exception("tmp archive generation failed")

            proc = run(
                [
                    "openssl",
                    "cms",
                    "-encrypt",
                    "-aes256",
                    "-in",
                    TMP_TMP_ARCHIVE_FILE,
                    "-binary",
                    "-outform",
                    "DER",
                    "-out",
                    DEBUG_TMP_ARCHIVE_FILE,
                    SystemSettingsManage.get_cert_for_file_encryption(),
                ],
                capture_output=True,
            )
            Path(TMP_TMP_ARCHIVE_FILE).unlink()
            if proc.returncode != 0:
                raise Exception(proc.stderr.decode("utf-8"))

            if not Path(DEBUG_TMP_ARCHIVE_FILE).exists():
                raise Exception("encrypted archive generation failed")

            return (True, "", DEBUG_TMP_ARCHIVE_FILE)
        except Exception as exception:
            msg = f"Unable to export debug info - {str(exception)}"
            result = (False, msg, None)
        return result

    @staticmethod
    async def imported_connection_exists(connection_file_path: Path) -> bool:
        """
        Determine whether or not the given imported network connection file matches an already
        existing network connection
        """
        if await NetworkService.connection_profile_exists_by_id(
            connection_file_path.stem
        ):
            return True

        parser = configparser.ConfigParser()
        parser.read(str(connection_file_path))
        if await NetworkService.connection_profile_exists_by_id(
            str(parser.get("connection", "id", fallback=""))
        ):
            return True

        return False

    @staticmethod
    def imported_connection_is_reserved(
        imported_connection_file_path: Path,
    ) -> bool:
        """
        Determine whether or not the given imported network connection file matches a reserved
        network connection (from /usr/lib/NetworkManager/system-connections)
        """
        imported_file_parser = configparser.ConfigParser()
        imported_file_parser.read(str(imported_connection_file_path))

        imported_file_id = str(
            imported_file_parser.get("connection", "id", fallback="")
        )
        if not imported_file_id:
            return False

        return NetworkService.connection_profile_is_reserved_by_id(imported_file_id)
