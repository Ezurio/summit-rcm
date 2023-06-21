"""
Module to interact with files.
"""

import os
from shutil import copy2, rmtree
from subprocess import run
from syslog import LOG_ERR, syslog
from typing import Any, List, Tuple
import aiofiles
import falcon.asgi
import falcon.media.multipart
from summit_rcm import definition
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
    async def handle_file_upload(
        incoming_data: falcon.asgi.multipart.BodyPart | bytes, path: str
    ) -> str:
        """
        Handle when a client uploads a file as either a multipart form part or raw bytes.
        """
        if isinstance(incoming_data, falcon.asgi.multipart.BodyPart):
            return await FilesService.handle_file_upload_multipart_form_part(
                incoming_data, path
            )

        if isinstance(incoming_data, bytes):
            return await FilesService.handle_file_upload_bytes(incoming_data, path)

        raise Exception("Invalid data type")

    @staticmethod
    async def handle_file_upload_multipart_form_part(
        part: falcon.asgi.multipart.BodyPart, path: str
    ) -> str:
        """
        Handle file upload as multipart form part
        """
        with open(path, "wb") as dest:
            while True:
                data = await part.stream.read(FILE_READ_SIZE)
                if not data:
                    break
                dest.write(data)
        return path

    @staticmethod
    async def handle_file_upload_bytes(data: bytes, path: str) -> str:
        """
        Handle file upload as bytes
        """
        with open(path, "wb") as dest:
            dest.write(data)
        return path

    @staticmethod
    async def handle_file_download(path: str) -> aiofiles.base.AiofilesContextManager:
        """
        Handle when a client downloads a file
        """
        if not os.path.isfile(path):
            raise Exception("File not found")

        return await aiofiles.open(path, "rb")

    @staticmethod
    async def handle_cert_file_upload(
        incoming_data: falcon.asgi.multipart.BodyPart | bytes, name: str
    ):
        """
        Handle when a client uploads a certificate file
        """
        return await FilesService.handle_file_upload(
            incoming_data,
            os.path.normpath(os.path.join(NETWORKMANAGER_DIR_FULL, "certs", name)),
        )

    @staticmethod
    async def handle_connection_import_file_upload(
        incoming_data: falcon.asgi.multipart.BodyPart | bytes,
    ):
        """
        Handle when a client uploads an archive for importing connections
        """
        return await FilesService.handle_file_upload(
            incoming_data, os.path.normpath(CONNECTION_TMP_ARCHIVE_FILE)
        )

    @staticmethod
    async def handle_config_import_file_upload(
        incoming_data: falcon.asgi.multipart.BodyPart | bytes,
    ):
        """
        Handle when a client uploads an archive for importing system configuration
        """
        return await FilesService.handle_file_upload(
            incoming_data, os.path.normpath(CONFIG_TMP_ARCHIVE_FILE)
        )

    @staticmethod
    def is_encrypted_storage_toolkit_enabled() -> bool:
        """
        Determines whether or not the Summit Encrypted Storage Toolkit is enabled on the running
        image.
        """
        return os.path.exists(FACTORY_RESET_SCRIPT)

    @staticmethod
    async def import_connections(password: str) -> Tuple[bool, str]:
        """
        Handle importing NetworkManager connections and certificates from a properly structured and
        encrypted zip archive

        Return value is a tuple in the form of: (success, message)
        """
        archive_upload_path = os.path.normpath(CONNECTION_TMP_ARCHIVE_FILE)
        if not os.path.isfile(archive_upload_path):
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
                    archive_upload_path,
                    "-d",
                    TMP_ARCHIVE_DIRECTORY,
                ],
                capture_output=True,
            )
            if proc.returncode != 0:
                raise Exception(proc.stderr.decode("utf-8"))

            # Verify expected sub directories ('system-connections' and 'certs') are present
            if not os.path.exists(
                os.path.join(
                    TMP_ARCHIVE_DIRECTORY,
                    NETWORKMANAGER_DIR,
                    "system-connections",
                )
            ) or not os.path.exists(
                os.path.join(
                    TMP_ARCHIVE_DIRECTORY,
                    NETWORKMANAGER_DIR,
                    "certs",
                )
            ):
                raise Exception("Expected files missing")

            # Copy connections and certs
            for subdir in ["system-connections", "certs"]:
                for file in os.listdir(
                    os.path.join(
                        TMP_ARCHIVE_DIRECTORY,
                        NETWORKMANAGER_DIR,
                        subdir,
                    )
                ):
                    try:
                        source = os.path.join(
                            TMP_ARCHIVE_DIRECTORY,
                            NETWORKMANAGER_DIR,
                            subdir,
                            file,
                        )
                        dest = os.path.join("/", NETWORKMANAGER_DIR, subdir, file)
                        if os.path.islink(dest):
                            continue
                        copy2(
                            source,
                            dest,
                            follow_symlinks=False,
                        )
                    except Exception:
                        pass

            # Requst NetworkManager to reload connections
            if not await NetworkManagerService().reload_connections():
                return (False, "Unable to reload connections after import")

            result = (True, "")
        except Exception as exception:
            result = (False, str(exception))
        finally:
            # Delete the temp file if present
            try:
                os.remove(archive_upload_path)
            except OSError:
                pass

            # Delete the temp dir if present
            try:
                rmtree(TMP_ARCHIVE_DIRECTORY, ignore_errors=True)
            except Exception as exception:
                msg = f"Error cleaning up connection imports: {str(exception)}"
                return (False, msg)

        return result

    @staticmethod
    def export_connections(password: str) -> Tuple[bool, str, Any]:
        """
        Handle exporting NetworkManager connections and certificates as a properly structured and
        encrypted zip archive

        Return value is a tuple in the form of: (success, message, archive_path)
        """
        archive_download_path = os.path.normpath(CONNECTION_TMP_ARCHIVE_FILE)
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
                    archive_download_path,
                    os.path.join("/", NETWORKMANAGER_DIR, "system-connections"),
                    os.path.join("/", NETWORKMANAGER_DIR, "certs"),
                ],
                capture_output=True,
            )
            if proc.returncode != 0:
                raise Exception(proc.stderr.decode("utf-8"))

            if not os.path.isfile(archive_download_path):
                raise Exception("archive generation failed")

            return (True, "", archive_download_path)
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
        for entry in os.scandir(definition.FILEDIR_DICT.get(file_type)):
            if entry.is_file():
                strs = entry.name.split(".")
                if len(strs) == 2 and strs[1] in definition.FILEFMT_DICT.get(file_type):
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
        path = os.path.normpath(os.path.join(NETWORKMANAGER_DIR_FULL, "certs", name))
        if not os.path.isfile(path):
            raise FileNotFoundError()

        os.remove(path)

    @staticmethod
    def export_system_config(password: str) -> Tuple[bool, str, Any]:
        """
        Handle exporting Summit RCM system configuration as a properly structured and encrypted zip
        archive.

        Return value is a tuple in the form of: (success, message, archive_path)
        """
        archive_download_path = os.path.normpath(CONFIG_TMP_ARCHIVE_FILE)
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
                    archive_download_path,
                    ".",
                ],
                cwd=definition.FILEDIR_DICT.get("config"),
                capture_output=True,
            )
            if proc.returncode != 0:
                raise Exception(proc.stderr.decode("utf-8"))

            if not os.path.isfile(archive_download_path):
                raise Exception("archive generation failed")

            return (True, "", archive_download_path)
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
        archive_upload_path = os.path.normpath(CONFIG_TMP_ARCHIVE_FILE)
        if not os.path.isfile(archive_upload_path):
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
                    archive_upload_path,
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
                    archive_upload_path,
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
                    archive_upload_path,
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
            try:
                os.remove(archive_upload_path)
            except OSError:
                pass

        return result

    @staticmethod
    def export_logs(password: str) -> Tuple[bool, str, Any]:
        """
        Handle exporting logs as a properly structured and encrypted zip archive.

        Return value is a tuple in the form of: (success, message, archive_path)
        """
        archive_download_path = os.path.normpath(LOG_TMP_ARCHIVE_FILE)
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
                    archive_download_path,
                    ".",
                ],
                cwd=FilesService.get_log_path(),
                capture_output=True,
            )
            if proc.returncode != 0:
                raise Exception(proc.stdout.decode("utf-8"))

            if not os.path.isfile(archive_download_path):
                raise Exception("archive generation failed")

            return (True, "", archive_download_path)
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
        archive_tmp_path = os.path.normpath(TMP_TMP_ARCHIVE_FILE)
        archive_download_path = os.path.normpath(DEBUG_TMP_ARCHIVE_FILE)
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
                    archive_tmp_path,
                ]
                + debug_paths,
                capture_output=True,
            )
            if proc.returncode != 0:
                raise Exception(proc.stderr.decode("utf-8"))

            if not os.path.isfile(archive_tmp_path):
                raise Exception("tmp archive generation failed")

            proc = run(
                [
                    "openssl",
                    "smime",
                    "-encrypt",
                    "-aes256",
                    "-in",
                    archive_tmp_path,
                    "-binary",
                    "-outform",
                    "DER",
                    "-out",
                    archive_download_path,
                    SystemSettingsManage.get_cert_for_file_encryption(),
                ],
                capture_output=True,
            )
            os.unlink(TMP_TMP_ARCHIVE_FILE)
            if proc.returncode != 0:
                raise Exception(proc.stderr.decode("utf-8"))

            if not os.path.isfile(archive_download_path):
                raise Exception("encrypted archive generation failed")

            return (True, "", archive_download_path)
        except Exception as exception:
            msg = f"Unable to export debug info - {str(exception)}"
            result = (False, msg, None)
        return result
