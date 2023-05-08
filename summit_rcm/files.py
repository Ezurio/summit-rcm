import os
from shutil import copy2, rmtree
from subprocess import run, call
from threading import Lock
from syslog import LOG_ERR, syslog
from typing import Any, List, Tuple
import falcon
from summit_rcm.services.system_service import FACTORY_RESET_SCRIPT
from summit_rcm.services.network_service import NetworkService
from . import definition
from .settings import SystemSettingsManage
import aiofiles

CONNECTION_TMP_ARCHIVE_FILE = "/tmp/archive.zip"
CONNECTION_TMP_ARCHIVE_DIRECTORY = "/tmp/import"
FILE_READ_SIZE = 8192
UNZIP = "/usr/bin/unzip"
ZIP = "/usr/bin/zip"
NETWORKMANAGER_DIR = "etc/NetworkManager"


class FileManage:
    """File Management"""

    _lock = Lock()
    FILE_MANAGE_SCRIPT = "/usr/bin/summit-rcm.scripts/summit-rcm_files.sh"
    FILE_MANAGE_POST_ZIP_TYPES = ["config", "timezone"]

    # log will be saved in /var/run/log/journal/ for volatile mode, or /var/log/journal/ for
    # persistent mode. If "/var/run/log/journal/" exists, it should be in volatile mode.
    _log_data_dir = "/var/run/log/journal/"
    if not os.path.exists("/var/run/log/journal/"):
        _log_data_dir = "/var/log/journal/"

    async def save_file(self, type, part):
        path = os.path.normpath(
            os.path.join(definition.FILEDIR_DICT[type], part.secure_filename)
        )
        try:
            async with aiofiles.open(path, "wb+") as dest:
                await part.stream.pipe(dest)
            return path
        except Exception:
            return None

    def is_encrypted_storage_toolkit_enabled(self) -> bool:
        return os.path.exists(FACTORY_RESET_SCRIPT)

    async def on_post(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"], "InfoMsg": ""}

        try:
            form = await req.get_media()
        except falcon.MediaNotFoundError as e:
            result["InfoMsg"] = f"Invalid request - {str(e.description)}"
            resp.media = result
            return

        if not isinstance(form, falcon.asgi.multipart.MultipartForm):
            result["InfoMsg"] = "Invalid request - multipart form required"
            resp.media = result
            return

        async for part in form:
            if part.name == "type":
                try:
                    type = await part.text
                except Exception:
                    type = None
                break

        if not type:
            syslog("FileManage POST - no type specified")
            result["InfoMsg"] = "file POST - no type specified"
            resp.media = result
            return

        if type not in definition.FILEDIR_DICT:
            syslog(f"FileManage POST type {type} unknown")
            result["InfoMsg"] = f"file POST type {type} unknown"  # bad request
            resp.media = result
            return

        async for part in form:
            if part.name == "file":
                if (
                    type in FileManage.FILE_MANAGE_POST_ZIP_TYPES
                    and not part.secure_filename.endswith(".zip")
                ):
                    syslog("FileManage POST type not .zip file")
                    result["InfoMsg"] = "file POST type not .zip file"  # bad request
                    resp.media = result
                    return

                try:
                    with FileManage._lock:
                        fp = await self.save_file(type, part)
                        if not fp:
                            syslog("FileManage POST type failure to copy file")
                            result[
                                "InfoMsg"
                            ] = "file POST failure to copy file"  # bad request
                            resp.media = result
                            return

                        if (
                            type == "config"
                            and not self.is_encrypted_storage_toolkit_enabled()
                        ):
                            syslog(
                                "FileManage POST - config import not available on non-encrypted file system images"
                            )
                            resp.status = falcon.HTTP_400
                            return

                        # Only attempt to unzip the uploaded file if the 'type' requires a zip file.
                        # Otherwise, just saving the file is sufficient (i.e., for a certificate)
                        if type in FileManage.FILE_MANAGE_POST_ZIP_TYPES:
                            password = req.params.get("password", "")
                            res = call(
                                [
                                    FileManage.FILE_MANAGE_SCRIPT,
                                    type,
                                    "unzip",
                                    fp,
                                    definition.FILEDIR_DICT.get(type),
                                    password,
                                ]
                            )
                            os.remove(fp)
                            if res:
                                syslog(
                                    f"unzip command file '{fp}' failed with error {res}"
                                )
                                result[
                                    "InfoMsg"
                                ] = f"unzip command failed to unzip provided file.  Error returned: {res}"  # Internal server error
                                resp.media = result
                                return

                        result["SDCERR"] = definition.SUMMIT_RCM_ERRORS[
                            "SDCERR_SUCCESS"
                        ]
                        resp.media = result
                        return
                except Exception:
                    syslog("unable to obtain FileManage._lock")
                    result[
                        "InfoMsg"
                    ] = "unable to obtain internal file lock"  # Internal server error
                    resp.media = result
                    return

        # The form is missing a 'file' part
        syslog("FileManage POST - no filename provided")
        result["InfoMsg"] = "file POST - no filename specified"
        resp.media = result
        return

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200

        type = req.params.get("type", None)
        if not type:
            syslog("FileManage Get - no filename provided")
            resp.status = falcon.HTTP_400
            return

        file = "{0}{1}".format(type, ".zip")
        path = "{0}{1}".format("/tmp/", file)

        if type == "config":

            password = req.params.get("password", None)
            if not password:
                syslog("FileManage Get - no password provided")
                resp.status = falcon.HTTP_400
                return

            if not self.is_encrypted_storage_toolkit_enabled():
                syslog(
                    "FileManage GET - config export not available on non-encrypted file system images"
                )
                resp.status = falcon.HTTP_400
                return

            args = [
                FileManage.FILE_MANAGE_SCRIPT,
                "config",
                "zip",
                definition.FILEDIR_DICT.get(type),
                path,
                password,
            ]
            syslog("Configuration zipped for user")
        elif type == "log":

            password = req.params.get("password", None)
            if not password:
                syslog("FileManage Get - no password provided")
                resp.status = falcon.HTTP_400
                return
            args = [
                FileManage.FILE_MANAGE_SCRIPT,
                "log",
                "zip",
                FileManage._log_data_dir,
                path,
                password,
            ]
            syslog("System log zipped for user")

        elif type == "debug":
            args = [
                FileManage.FILE_MANAGE_SCRIPT,
                "debug",
                "zip",
                " ".join([FileManage._log_data_dir, definition.FILEDIR_DICT["config"]]),
                path,
                SystemSettingsManage.get_cert_for_file_encryption(),
            ]
            syslog("Configuration and system log zipped/encrypted for user")
        else:
            syslog(f"FileManage GET - unknown file type {type}")
            resp.status = falcon.HTTP_400
            return

        try:
            call(args)
        except Exception as e:
            syslog("Script execution error {}".format(e))
            resp.status = falcon.HTTP_400
            return

        if os.path.isfile(path):
            resp.content_type = falcon.MEDIA_TEXT
            with open(path, "rb") as obj_file:
                resp.text = obj_file.read()
            os.unlink(path)
            return

        syslog(f"Failed to create file {path} for user")
        resp.status = falcon.HTTP_500

    async def on_delete(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Unable to delete file",
        }
        type = req.params.get("type", None)
        file = req.params.get("file", None)
        if not type or not file:
            if not type:
                syslog("FileManage DELETE - no type specified")
                result["InfoMsg"] = "no type specified"
            if not file:
                syslog("FileManage DELETE - no filename provided")
                result["InfoMsg"] = "no file specified"
            resp.media = result
            return
        valid = ["cert", "pac"]
        if type not in valid:
            result["InfoMsg"] = f"type not one of {valid}"
            resp.media = result
            return
        path = os.path.normpath(os.path.join(definition.FILEDIR_DICT[type], file))
        if os.path.isfile(path):
            os.remove(path)
            if not os.path.exists(path):
                result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
                result["InfoMsg"] = f"file {file} deleted"
                syslog(f"file {file} deleted")
            else:
                syslog(f"Attempt to remove file {path} did not succeed")
        else:
            syslog(f"Attempt to remove non-existant file {path}")
            result["InfoMsg"] = f"File: {file} not present"
        resp.media = result
        return


class FilesManage:
    async def import_connections(
        self, import_archive: falcon.media.multipart.BodyPart, password: str
    ) -> Tuple[bool, str]:
        """
        Handle importing NetworkManager connections and certificates from a properly structured and
        encrypted zip archive

        Return value is a tuple in the form of: (success, message)
        """
        if not import_archive:
            return (False, "Invalid archive")

        archive_download_path = os.path.normpath(CONNECTION_TMP_ARCHIVE_FILE)
        result = (False, "Unknown error")
        try:
            # Save the archive to /tmp
            with open(archive_download_path, "wb") as archive_file:
                while True:
                    data = import_archive.stream.read(FILE_READ_SIZE)
                    if not data:
                        break
                    archive_file.write(data)

            # Extract the archive using 'unzip' (the built-in Python zipfile implementation is
            # handled in pure Python, is "extremely slow", and does not support generating
            # encrypted archives.
            # https://docs.python.org/3/library/zipfile.html
            proc = run(
                [
                    UNZIP,
                    "-P",
                    password,
                    "-n",
                    archive_download_path,
                    "-d",
                    CONNECTION_TMP_ARCHIVE_DIRECTORY,
                ],
                capture_output=True,
            )
            if proc.returncode != 0:
                raise Exception(proc.stderr.decode("utf-8"))

            # Verify expected sub directories ('system-connections' and 'certs') are present
            if not os.path.exists(
                os.path.join(
                    CONNECTION_TMP_ARCHIVE_DIRECTORY,
                    NETWORKMANAGER_DIR,
                    "system-connections",
                )
            ) or not os.path.exists(
                os.path.join(
                    CONNECTION_TMP_ARCHIVE_DIRECTORY,
                    NETWORKMANAGER_DIR,
                    "certs",
                )
            ):
                raise Exception("Expected files missing")

            # Copy connections and certs
            for subdir in ["system-connections", "certs"]:
                for file in os.listdir(
                    os.path.join(
                        CONNECTION_TMP_ARCHIVE_DIRECTORY,
                        NETWORKMANAGER_DIR,
                        subdir,
                    )
                ):
                    try:
                        source = os.path.join(
                            CONNECTION_TMP_ARCHIVE_DIRECTORY,
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
            if not await NetworkService.reload_nm_connections():
                return (False, "Unable to reload connections after import")

            result = (True, "")
        except Exception as e:
            result = (False, str(e))
        finally:
            # Delete the temp file if present
            try:
                os.remove(archive_download_path)
            except OSError:
                pass

            # Delete the temp dir if present
            try:
                rmtree(CONNECTION_TMP_ARCHIVE_DIRECTORY, ignore_errors=True)
            except Exception as e:
                msg = f"Error cleaning up connection imports: {str(e)}"
                return (False, msg)

            return result

    def export_connections(self, password: str) -> Tuple[bool, str, Any]:
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
            # encrypted archives.
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
        except Exception as e:
            msg = f"Unable to export connections - {str(e)}"
            syslog(LOG_ERR, msg)
            result = (False, msg, None)
        return result

    @staticmethod
    def get_cert_or_pac_files(type: str) -> List[str]:
        """Retrieve a list of files of the specified type ('cert' or 'pac')"""
        if type not in ["cert", "pac"]:
            return []

        files = []
        with os.scandir(definition.FILEDIR_DICT.get(type)) as listOfEntries:
            for entry in listOfEntries:
                if entry.is_file():
                    strs = entry.name.split(".")
                    if len(strs) == 2 and strs[1] in definition.FILEFMT_DICT.get(type):
                        files.append(entry.name)
        files.sort()
        return files

    # Since we sometimes return a binary file and sometimes return JSON with the GET endpoint, we
    # can't use the @cherrypy.tools.json_out() decorator here. Therefore, we have to mimick this
    # logic when returning JSON.
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        result = {
            "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "",
            "count": 0,
            "files": [],
        }
        type = req.params.get("type", None)
        valid = ["cert", "pac", "network"]
        if not type:
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
            result["InfoMsg"] = "no filename provided"
            resp.content_type = falcon.MEDIA_JSON
            resp.media = result
            return
        if type not in valid:
            result["InfoMsg"] = f"type not one of {valid}"
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
            resp.content_type = falcon.MEDIA_JSON
            resp.media = result
            return

        if type == "network":
            password = req.params.get("password", "")
            if not password or password == "":
                result["InfoMsg"] = "Invalid password"
                resp.content_type = falcon.MEDIA_JSON
                resp.media = result
                return

            success, msg, archive = self.export_connections(password)
            if success:
                resp.content_type = falcon.MEDIA_TEXT
                with open(archive, "rb") as obj_file:
                    resp.text = obj_file.read()
                os.unlink(archive)
                return
            else:
                syslog(LOG_ERR, f"Could not export connections - {msg}")
                resp.status = falcon.HTTP_500
                return
        else:
            files = FilesManage.get_cert_or_pac_files(type)
            result["files"] = files
            result["count"] = len(files)
            result["InfoMsg"] = f"{type} files"
        resp.content_type = falcon.MEDIA_JSON
        resp.media = result

    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"], "InfoMsg": ""}

        type = req.params.get("type", None)
        valid_types = ["network"]
        if not type or type not in valid_types:
            result["InfoMsg"] = "Invalid file type"
            resp.media = result
            return

        archive = None
        for part in await req.get_media():
            if part.name == "archive":
                archive = part
                break

        if not archive:
            result["InfoMsg"] = "Invalid archive"
            resp.media = result
            return

        password = req.params.get("password", "")
        if not password or password == "":
            result["InfoMsg"] = "Invalid password"
            resp.media = result
            return

        success, msg = await self.import_connections(archive, password)
        if success:
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        else:
            syslog(LOG_ERR, f"Could not import connections - {msg}")
            result["InfoMsg"] = f"Could not import connections - {msg}"

        resp.media = result
