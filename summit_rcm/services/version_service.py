#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to retrieve version info
"""

import asyncio
import os
import re
from syslog import LOG_ERR, syslog
from subprocess import run, TimeoutExpired

try:
    import aiofiles
except ImportError as error:
    # Ignore the error if the aiofiles module is not available if generating documentation
    if os.environ.get("DOCS_GENERATION") != "True":
        raise error
from asyncio import create_subprocess_exec, subprocess
from summit_rcm.services.network_manager_service import (
    NMDeviceType,
    NetworkManagerService,
)
from summit_rcm import definition
from summit_rcm.settings import SystemSettingsManage
from summit_rcm.utils import (
    Singleton,
    get_current_side,
    get_next_side,
    get_base_hw_part_number,
)

SDCSUPP_VERSION_REG_EXP = r"sdcsupp\s+v(?P<VERSION>.*)"
NMCLI_VERSION_REG_EXP = r"nmcli.*version\s+(?P<VERSION>.*)"


class VersionService(metaclass=Singleton):
    """Service to retrieve version info"""

    _version = {}

    async def get_version(self, is_legacy: bool = False) -> dict:
        """Retrieve the system version info"""
        try:
            if not self._version:
                # Note: The NetworkManager version is retrieved from the nmcli tool instead of the
                # D-Bus API because the D-Bus API "Version" property does not provide the radio
                # stack version (it's derived from "VERSION" instead of "NM_DIST_VERSION" in the
                # NetworkManager sources).
                nm_version = await self.get_nmcli_version()

                self._version["nmVersion"] = nm_version
                self._version["summitRcm"] = definition.SUMMIT_RCM_VERSION
                self._version["build"] = await self.get_os_release_version()
                self._version["supplicant"] = await self.get_supplicant_version()
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
                try:
                    self._version["currentSide"] = await get_current_side()
                except ValueError:
                    self._version["currentSide"] = "sd"
                self._version["baseHwPartNumber"] = await get_base_hw_part_number()
            self._version["nextSide"] = (
                "sd" if self._version["currentSide"] == "sd" else await get_next_side()
            )

            if is_legacy:
                # Adjust property names for legacy support
                version_legacy = self._version.copy()
                version_legacy["u-boot"] = version_legacy.pop("uBoot")
                version_legacy["nm_version"] = version_legacy.pop("nmVersion")
                version_legacy["summit_rcm"] = version_legacy.pop("summitRcm")
                version_legacy["radio_stack"] = version_legacy.pop("radioStack")
                version_legacy["kernel_vermagic"] = version_legacy.pop("kernelVermagic")
                version_legacy["current_side"] = version_legacy.pop("currentSide")
                version_legacy["next_side"] = version_legacy.pop("nextSide")
                version_legacy["base_hw_part_number"] = version_legacy.pop(
                    "baseHwPartNumber"
                )
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

    @staticmethod
    async def get_supplicant_version() -> str:
        """
        Retrieve the supplicant version

        Example 'sdcsupp -v' output: "sdcsupp v12.0.0.113-40.3.25.3"
        """
        proc = await asyncio.create_subprocess_exec(
            *["sdcsupp", "-v"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        match = re.search(SDCSUPP_VERSION_REG_EXP, stdout.decode("utf-8").strip())
        if match:
            return match.group("VERSION")

        return ""

    @staticmethod
    async def get_nmcli_version() -> str:
        """
        Retrieve the nmcli version

        Example 'nmcli --version' output: "nmcli tool, version 12.0.0.113-1.46.2"
        """
        proc = await asyncio.create_subprocess_exec(
            *["nmcli", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        match = re.search(NMCLI_VERSION_REG_EXP, stdout.decode("utf-8").strip())
        if match:
            return match.group("VERSION")
