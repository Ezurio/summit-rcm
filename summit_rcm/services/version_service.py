"""
Module to retrieve version info
"""

import os
import re
from syslog import LOG_ERR, syslog
from subprocess import run, TimeoutExpired, check_output
import aiofiles
from asyncio import create_subprocess_exec, subprocess
from summit_rcm.services.network_manager_service import (
    NMDeviceType,
    NetworkManagerService,
)
from summit_rcm import definition
from summit_rcm.settings import SystemSettingsManage
from summit_rcm.utils import Singleton


class VersionService(metaclass=Singleton):
    """Service to retrieve version info"""

    _version = {}

    async def get_version(self, is_legacy: bool = False) -> dict:
        """Retrieve the system version info"""
        try:
            if not self._version:
                network_manager_props = (
                    await NetworkManagerService().get_obj_properties(
                        NetworkManagerService().NM_CONNECTION_MANAGER_OBJ_PATH,
                        NetworkManagerService().NM_CONNECTION_MANAGER_IFACE,
                    )
                )
                nm_version = (
                    network_manager_props["Version"]
                    if network_manager_props.get("Version", None) is not None
                    else ""
                )
                self._version["nmVersion"] = str(nm_version)
                self._version["summitRcm"] = definition.SUMMIT_RCM_VERSION
                self._version["build"] = await self.get_os_release_version()
                self._version["supplicant"] = (
                    check_output(["sdcsupp", "-v"]).decode("ascii").rstrip()
                )
                self._version["radioStack"] = str(nm_version).partition("-")[0]
                for dev_obj_path in await NetworkManagerService().get_all_devices():
                    dev_props = await NetworkManagerService().get_obj_properties(
                        dev_obj_path, NetworkManagerService().NM_DEVICE_IFACE
                    )
                    dev_type = (
                        dev_props["DeviceType"]
                        if dev_props.get("DeviceType", None) is not None
                        else NMDeviceType.NM_DEVICE_TYPE_UNKNOWN
                    )
                    if dev_type == NMDeviceType.NM_DEVICE_TYPE_WIFI:
                        self._version["driver"] = dev_props.get("Driver", "")
                        self._version["kernelVermagic"] = dev_props.get(
                            "DriverVersion", ""
                        )
                        break
                try:
                    self._version["bluez"] = self.get_bluez_version()
                except Exception:
                    self._version["bluez"] = "n/a"
                self._version["uBoot"] = await self.get_uboot_version()

            if is_legacy:
                # Adjust property names for legacy support
                version_legacy = self._version.copy()
                version_legacy["u-boot"] = version_legacy.pop("uBoot")
                version_legacy["nm_version"] = version_legacy.pop("nmVersion")
                version_legacy["summit_rcm"] = version_legacy.pop("summitRcm")
                version_legacy["radio_stack"] = version_legacy.pop("radioStack")
                version_legacy["kernel_vermagic"] = version_legacy.pop("kernelVermagic")
                return version_legacy

            return self._version
        except Exception as exception:
            syslog(f"Error reading version info: {str(exception)}")
            return {}

    @staticmethod
    def get_bluez_version() -> str:
        """
        Retrieve the current version of BlueZ as a string by running 'bluetoothctl --version'
        """
        BLUEZ_VERSION_RE = r"bluetoothctl: (?P<VERSION>.*)"
        BLUETOOTHCTL_PATH = "/usr/bin/bluetoothctl"

        if not os.path.exists(BLUETOOTHCTL_PATH):
            return "Unknown"

        try:
            proc = run(
                [BLUETOOTHCTL_PATH, "--version"],
                capture_output=True,
                timeout=SystemSettingsManage.get_user_callback_timeout(),
            )

            if not proc.returncode:
                for line in proc.stdout.decode("utf-8").splitlines():
                    line = line.strip()
                    match = re.match(BLUEZ_VERSION_RE, line)
                    if match:
                        return str(match.group("VERSION"))
        except TimeoutExpired:
            syslog(LOG_ERR, "Call to 'bluetoothctl --version' timeout")
        except Exception as exception:
            syslog(
                LOG_ERR, f"Call to 'bluetoothctl --version' failed: {str(exception)}"
            )

        return "Unknown"

    @staticmethod
    async def get_os_release_version() -> str:
        """Retrieve the current OS release version string from the /etc/os-release file"""
        OS_RELEASE_FILE = "/etc/os-release"
        OS_RELEASE_VERSION_RE = r"VERSION=\"(?P<VERSION>.*)\""

        async with aiofiles.open(OS_RELEASE_FILE, "r") as os_release_file:
            for line in await os_release_file.readlines():
                match = re.match(OS_RELEASE_VERSION_RE, line)
                if match:
                    return str(match.group("VERSION"))

        return "Unknown"

    @staticmethod
    async def get_uboot_version() -> str:
        """Retrieve the current u-boot version"""
        try:
            proc = await create_subprocess_exec(
                *["fw_printenv", "-n", "version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise Exception(stderr.decode("utf-8").strip())
            return stdout.decode("utf-8").strip()
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to read uboot version: {str(exception)}")
            return ""
