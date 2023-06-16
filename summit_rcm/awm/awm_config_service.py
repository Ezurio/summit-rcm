"""
Module to support configuration of AWM.
"""

import os
from syslog import syslog
from threading import Lock
import libconf
from summit_rcm.utils import Singleton
from summit_rcm.settings import ServerConfig


ADAPTIVE_WW_CONFIG_FILE = "/etc/default/adaptive_ww"


class AWMConfigService(metaclass=Singleton):
    """
    Exposes functionality to get/set AWM configuration.
    """

    _lock = Lock()

    def get_scan_attempts(self) -> int:
        """
        Retrieve any configured value for 'scan_attempts', and if not found, raise an exception.
        """

        # Check if there is a configuration file which contains a "scan_attempts:0" entry
        # if configuration file does not exist, scan_attempts is not disabled
        f = ServerConfig().get_parser()["summit-rcm"].get("awm_cfg", None).strip('"')
        if not f or not os.path.isfile(f):
            raise Exception("Not found")

        with self._lock:
            with open(f, "r", encoding="utf-8") as fp:
                config = libconf.load(fp)
            if "scan_attempts" in config:
                return config["scan_attempts"]

        raise Exception("Not found")

    def set_scan_attempts(self, geolocation_scanning_enable: int):
        """
        Attempt to configure 'scan_attempts' and raise an exception if unable to do so.
        """

        # Check if there is a configuration file which contains a "scan_attempts:0" entry
        # if writable configuration file does not exist, scan_attempts can not be modified

        f = ServerConfig().get_parser()["summit-rcm"].get("awm_cfg", None).strip('"')
        if not f:
            raise Exception("Not found")

        os.makedirs(os.path.dirname(f), exist_ok=True)

        with self._lock:
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

    @staticmethod
    def get_lite_mode_enabled() -> bool:
        """Get whether or not "LITE" mode is enabled."""
        try:
            with open(ADAPTIVE_WW_CONFIG_FILE, "r") as file:
                if "LITE" in file.read():
                    return True
        except Exception as exception:
            syslog(f"Unable to read adaptive_ww config file: {str(exception)}")

        return False
