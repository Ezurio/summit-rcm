import falcon
import subprocess
from summit_rcm.services.network_manager_service import (
    NMDeviceType,
    NetworkManagerService,
)
from summit_rcm import definition


class Version:
    _version = {}

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        try:
            if not Version._version:
                Version._version["SDCERR"] = definition.SUMMIT_RCM_ERRORS[
                    "SDCERR_SUCCESS"
                ]
                Version._version["InfoMsg"] = ""
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
                Version._version["nm_version"] = str(nm_version)
                Version._version["summit_rcm"] = definition.SUMMIT_RCM_VERSION
                Version._version["build"] = (
                    subprocess.check_output(
                        "sed -n 's/^VERSION=//p' /etc/os-release", shell=True
                    )
                    .decode("ascii")
                    .strip()
                    .strip('"')
                )
                Version._version["supplicant"] = (
                    subprocess.check_output(["sdcsupp", "-v"]).decode("ascii").rstrip()
                )
                Version._version["radio_stack"] = str(nm_version).partition("-")[0]
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
                        Version._version["driver"] = dev_props.get("Driver", "")
                        Version._version["kernel_vermagic"] = dev_props.get(
                            "DriverVersion", ""
                        )
                        break
                # Version._version["bluez"] = (
                #     Bluetooth.get_bluez_version()
                #     if Bluetooth is not None
                #     else "n/a"
                # )
                Version._version["bluez"] = "n/a"
        except Exception as e:
            Version._version = {
                "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
                "InfoMsg": f"An exception occurred while trying to get versioning info: {e}",
            }
        resp.media = Version._version
