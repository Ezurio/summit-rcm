"""
Module to interact with files.
"""

import configparser
from shutil import copy2, rmtree
from subprocess import run
from syslog import LOG_ERR, syslog
from typing import Any, List, Tuple
from pathlib import Path
import aiofiles
from summit_rcm import definition
from summit_rcm.services.network_service import (
    ConnectionProfileReservedError,
    NetworkService,
)
from summit_rcm.settings import SystemSettingsManage
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
SUMMIT_RCM_DIR = "/etc/summit-rcm/"
DATA_SECRET_NETWORKMANAGER_DIR = "/data/secret/NetworkManager"
DATA_SECRET_SUMMIT_RCM_DIR = "/data/secret/summit-rcm"


class FilesService(metaclass=Singleton):
    """
    Service to interact with files.
    """

    @staticmethod
    def get_log_path() -> str:
        """Retrieve the path to where system logs are stored"""
        # Logs will be saved in /var/run/log/journal/ for volatile mode, or /var/log/journal/ for
        # persistent mode. If "/var/run/log/journal/" exists, it should be in volatile mode.
        return (
            "/var/run/log/journal/"
            if FilesService.is_encrypted_storage_toolkit_enabled()
            else "/var/log/journal/"
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
    async def handle_file_download(path: str) -> aiofiles.base.AiofilesContextManager:
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

            # Copy connections and certs
            for subdir in ["system-connections", "certs"]:
                for file in Path(
                    TMP_ARCHIVE_DIRECTORY, NETWORKMANAGER_DIR, subdir
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

                        dest = Path("/", NETWORKMANAGER_DIR, subdir, file.name)
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

            # Requst NetworkManager to reload connections
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
        path = Path(NETWORKMANAGER_DIR_FULL, "certs", name)
        if not path.exists():
            raise FileNotFoundError()

        path.unlink()

    @staticmethod
    def export_system_config(password: str) -> Tuple[bool, str, Any]:
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
            proc = run(
                [
                    ZIP,
                    "--symlinks",
                    "-P",
                    password,
                    "-9",
                    "-r",
                    CONFIG_TMP_ARCHIVE_FILE,
                    ".",
                ],
                cwd=definition.FILEDIR_DICT.get("config"),
                capture_output=True,
            )
            if proc.returncode != 0:
                raise Exception(proc.stderr.decode("utf-8"))

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
            proc = run(
                [
                    UNZIP,
                    "-P",
                    "1234",
                    "-t",
                    CONFIG_TMP_ARCHIVE_FILE,
                ],
                capture_output=True,
                cwd=definition.FILEDIR_DICT.get("config"),
            )
            if proc.returncode != 1:
                raise Exception("archive not encrypted")

            # Test that the password is correct
            proc = run(
                [
                    UNZIP,
                    "-P",
                    password,
                    "-t",
                    CONFIG_TMP_ARCHIVE_FILE,
                ],
                capture_output=True,
                cwd=definition.FILEDIR_DICT.get("config"),
            )
            if proc.returncode != 0:
                raise Exception("incorrect password")

            # Remove current config settings
            rmtree(DATA_SECRET_NETWORKMANAGER_DIR, ignore_errors=True)
            rmtree(DATA_SECRET_SUMMIT_RCM_DIR, ignore_errors=True)

            # Extract the archive using 'unzip' (the built-in Python zipfile implementation is
            # handled in pure Python, is "extremely slow", and does not support generating
            # encrypted archives).
            # https://docs.python.org/3/library/zipfile.html
            proc = run(
                [
                    UNZIP,
                    "-P",
                    password,
                    "-o",
                    CONFIG_TMP_ARCHIVE_FILE,
                ],
                capture_output=True,
                cwd=definition.FILEDIR_DICT.get("config"),
            )
            if proc.returncode != 0:
                raise Exception(proc.stdout.decode("utf-8"))

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
            debug_paths: list[str] = [FilesService.get_log_path()]
            if FilesService.is_encrypted_storage_toolkit_enabled():
                debug_paths.append(definition.FILEDIR_DICT.get("config"))
            else:
                debug_paths.extend([NETWORKMANAGER_DIR_FULL, SUMMIT_RCM_DIR])

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
                    "smime",
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
