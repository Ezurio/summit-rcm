import os
from threading import Lock

import falcon
import libconf

from .. import definition
from ..settings import ServerConfig


class AWMCfgManage(object):

    _lock = Lock()

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON

        # Infinite geo-location checks by default
        result = {
            "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "AWM configuration only supported in LITE mode",
            "geolocation_scanning_enable": 1,
        }

        # check if there is a configuration file which contains a "scan_attempts:0" entry
        # if configuration file does not exist, scan_attempts is not disabled
        f = ServerConfig().get_parser()["summit-rcm"].get("awm_cfg", None).strip('"')
        if not f or not os.path.isfile(f):
            resp.media = result
            return

        with AWMCfgManage._lock:
            with open(f, "r", encoding="utf-8") as fp:
                config = libconf.load(fp)
            if "scan_attempts" in config:
                result["geolocation_scanning_enable"] = config["scan_attempts"]
                result["InfoMsg"] = ""

        resp.media = result

    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON

        # Enable/disable geolocation scanning
        # 0: disable geolocation scanning
        # others: enable geolocation scanning
        result = {
            "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "AWM's geolocation scanning configuration only supported in LITE mode",
            "geolocation_scanning_enable": 1,
        }

        # determine if in LITE mode
        litemode = False
        with open("/etc/default/adaptive_ww", "r") as file:
            if "LITE" in file.read():
                litemode = True

        if not litemode:
            resp.media = result
            return

        # prep for next error condition
        result["InfoMsg"] = "No writable configuration file found"
        # check if there is a configuration file which contains a "scan_attempts:0" entry
        # if writable configuration file does not exist, scan_attempts can not be modified

        f = ServerConfig().get_parser()["summit-rcm"].get("awm_cfg", None).strip('"')
        if not f:
            resp.media = result
            return

        os.makedirs(os.path.dirname(f), exist_ok=True)

        put_data = await req.get_media()
        geolocation_scanning_enable = put_data.get("geolocation_scanning_enable", 0)

        with AWMCfgManage._lock:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    config = libconf.load(fp)
            except Exception:
                config = {}

            need_store = False
            if geolocation_scanning_enable:
                if "scan_attempts" in config:
                    del config["scan_attempts"]
                    need_store = True
            else:
                config["scan_attempts"] = geolocation_scanning_enable
                need_store = True

            if need_store:
                with open(f, "w", encoding="utf-8") as fp:
                    libconf.dump(config, fp)

        result["geolocation_scanning_enable"] = geolocation_scanning_enable
        result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        result["InfoMsg"] = ""
        resp.media = result
