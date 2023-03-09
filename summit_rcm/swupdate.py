import logging
from subprocess import Popen
from syslog import syslog, LOG_ERR
from typing import Tuple, Optional

import falcon
import swclient

from . import swuclient
from .somutil import get_current_side

swclient_fd: int = -1


class SWUpdate(object):
    FW_UPDATE_SCRIPT = "fw_update"

    SWU_SDCERR_UPDATED = 0
    SWU_SDCERR_FAIL = 1
    SWU_SDCERR_NOT_UPDATING = 2
    SWU_SDCERR_UPDATING = 5

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.swupdate_client = None
        self.proc: Optional[Popen[str]] = None
        self.status = self.SWU_SDCERR_NOT_UPDATING

    def log_exception(self, e, message: str = ""):
        self._logger.exception(e)
        syslog(LOG_ERR, message + str(e))

    def get_running_mode_for_update(self, image):
        try:
            running_mode = image + "-b" if get_current_side() == "a" else image + "-a"
        except Exception as e:
            self.log_exception(e)
            raise e

        return running_mode

    def get_update_status(self) -> Tuple[int, str]:
        try:
            info = ""
            if self.status == self.SWU_SDCERR_UPDATED:
                info = "Updated"
            elif self.status == self.SWU_SDCERR_FAIL:
                info = "Failed"
            elif self.status == self.SWU_SDCERR_NOT_UPDATING:
                info = "No update in progress"
            elif self.status == self.SWU_SDCERR_UPDATING:
                info = "Updating..."
            return self.status, info

        except Exception as e:
            self.log_exception(e)
            return self.SWU_SDCERR_FAIL, f"Error: {str(e)}"

    def recv_handler(self, status, rcurr_img, msg):
        if status in [swuclient.SWU_STATUS_SUCCESS, swuclient.SWU_STATUS_FAILURE]:
            # See swupdate-progress.c
            # Latch success & failure messages, ignoring all others.
            if status == swuclient.SWU_STATUS_SUCCESS:
                self.status = self.SWU_SDCERR_UPDATED
            elif status == swuclient.SWU_STATUS_FAILURE:
                self.status = self.SWU_SDCERR_FAIL
            # Close down the thread after completion
            self.stop_progress_thread()

    def stop_progress_thread(self):
        """stop the progress thread"""
        if self.swupdate_client:
            self.swupdate_client.stop_progress_thread()

    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200

        if not req.content_type or req.content_type != "application/octet-stream":
            resp.status = falcon.HTTP_415
            resp.text = "Expected an application/octet-stream content type"
            return

        if not req.content_length:
            resp.status = falcon.HTTP_411
            return

        try:
            data = await req.stream.read()
            if swclient_fd < 0:
                syslog(LOG_ERR, "swupdate.py: no update in progress")
                resp.status = falcon.HTTP_500
                resp.text = "Software Update error: no update in progress"
                return
            rc = swclient.do_fw_update(data, swclient_fd)
            if rc < 0:
                syslog(
                    LOG_ERR,
                    f"swclient.do_firmware_update returned {rc} while processing octet stream",
                )
                resp.status = falcon.HTTP_500
                resp.text = f"Software Update received error: {rc} while updating"
                return
        except Exception as e:
            syslog(LOG_ERR, f"Software Update error: {str(e)}")
            resp.status = falcon.HTTP_500
            resp.text = f"Software Update error: {str(e)}"

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 1, "InfoMsg": "Device is busy"}

        try:
            (result["SDCERR"], result["InfoMsg"]) = self.get_update_status()
        except Exception as e:
            self.log_exception(e)
            result["InfoMsg"] = f"Error: {str(e)}"

        resp.media = result

    async def on_post(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        global swclient_fd
        dryrun = 0

        result = {
            "SDCERR": 1,
            "InfoMsg": "Device is busy updating.",
        }

        def do_swupdate(
            args,
        ):
            try:
                # close_fds prevents hang on service stop
                self.proc = Popen(args, close_fds=True)
                result["InfoMsg"] = ""
                result["SDCERR"] = 0
            except Exception as e:
                self.log_exception(e)
                result["InfoMsg"] = "{}".format(e)

        if self.swupdate_client and self.swupdate_client.update_in_progress:
            resp.media = result
            return

        post_data = await req.get_media()
        url = post_data.get("url", None)
        if url and " " in url:
            result["InfoMsg"] = "Invalid URL"
            resp.media = result
            return
        image = post_data.get("image", "main")
        running_mode = self.get_running_mode_for_update(image)

        try:
            if self.swupdate_client is None:
                self.swupdate_client = swuclient.SWUpdateClient(self.recv_handler)
            else:
                self.swupdate_client.state = None
            if self.swupdate_client.open_ipc() < 0:
                return
            if url:
                do_swupdate(
                    args=[SWUpdate.FW_UPDATE_SCRIPT, "-x", "r", "-m", image, url],
                )
            else:
                swclient_fd = swclient.prepare_fw_update(dryrun, "stable", running_mode)
                if swclient_fd > 0:
                    result["InfoMsg"] = ""
                    result["SDCERR"] = 0
            self.swupdate_client.start_progress_thread(swclient_fd)
        except Exception as e:
            self.log_exception(e)
            result["InfoMsg"] = "{}".format(e)

        if result["SDCERR"]:
            self.stop_progress_thread()
        else:
            # In order to avoid race condition between first update coming from swupdate_client and
            # external REST query, just assume update started unless/until a failure or completion
            # occurs.
            self.status = self.SWU_SDCERR_UPDATING

        resp.media = result

    async def on_delete(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 0, "InfoMsg": ""}
        try:
            self.stop_progress_thread()
        except Exception as e:
            self.log_exception(e)
            result["SDCERR"] = 1
            result["InfoMsg"] = "{}".format(e)
        resp.media = result
