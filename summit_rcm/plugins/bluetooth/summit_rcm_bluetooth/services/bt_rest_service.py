#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""Module to support Bluetooth REST requests"""

from typing import Optional, List
import falcon.asgi
from summit_rcm import definition
from summit_rcm_bluetooth.services.ble import (
    ADAPTER_IFACE,
    BLUEZ_SERVICE_NAME,
    DEVICE_IFACE,
    find_device,
    find_devices,
    uri_to_uuid,
    controller_pretty_name,
)
from summit_rcm_bluetooth.services.bt import (
    CACHED_ADAPTER_PROPS,
    CACHED_DEVICE_PROPS,
    PASS_ADAPTER_PROPS,
    Bluetooth,
    get_controller_obj,
    lower_camel_case,
)
from summit_rcm.dbus_manager import DBusManager


class BluetoothRESTService:
    """Service to handle incoming REST requests"""

    @staticmethod
    def prepare_response_media(media: dict, is_legacy: bool = False) -> dict:
        """
        Remove the 'InfoMsg' and 'SDCERR' items from the response dictionary for non-legacy
        responses
        """
        if is_legacy:
            return media

        if "InfoMsg" in media:
            del media["InfoMsg"]
        if "SDCERR" in media:
            del media["SDCERR"]

        return media

    @staticmethod
    async def handle_get(
        req: falcon.asgi.Request,
        resp: falcon.asgi.Response,
        controller_name: str,
        device: str,
        is_legacy: bool = False,
    ) -> falcon.asgi.Response:
        """GET handler"""
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "",
        }

        try:
            filters: Optional[List[str]] = None
            if "filter" in req.params:
                filters = req.params["filter"].split(",")

            controller_friendly_name: str = (
                controller_pretty_name(controller_name) if controller_name else ""
            )

            device_uuid = uri_to_uuid(device) if device else None

            # get the system bus
            bus = await DBusManager().get_bus()
            # get the ble controller
            if controller_friendly_name:
                controller = (
                    controller_friendly_name,
                    await Bluetooth().get_remapped_controller(controller_friendly_name),
                )
                controllers = [controller]
                if not controller[1]:
                    if is_legacy:
                        result[
                            "InfoMsg"
                        ] = f"Controller {controller_friendly_name} not found."
                        resp.media = result
                        return
                    resp.status = falcon.HTTP_404
                    return
            else:
                controllers = {
                    (x, await Bluetooth().get_remapped_controller(x))
                    for x in Bluetooth().controller_addresses.keys()
                }

            for controller_friendly_name, controller in controllers:
                controller_result = {}
                try:
                    controller_obj = bus.get_proxy_object(
                        BLUEZ_SERVICE_NAME,
                        controller,
                        await bus.introspect(BLUEZ_SERVICE_NAME, controller),
                    )
                except Exception:
                    if is_legacy:
                        result[
                            "InfoMsg"
                        ] = f"Controller {controller_friendly_name} not found."
                        resp.media = result
                        return
                    resp.status = falcon.HTTP_404
                    return

                matched_filter = False
                if not device_uuid:
                    if not filters or "bluetoothDevices" in filters:
                        controller_result["bluetoothDevices"] = await find_devices(bus)
                        matched_filter = True

                    adapter_iface = controller_obj.get_interface(ADAPTER_IFACE)

                    if not filters or "transportFilter" in filters:
                        controller_result[
                            "transportFilter"
                        ] = Bluetooth().get_adapter_transport_filter(
                            controller_friendly_name
                        )
                        matched_filter = True

                    for pass_property in PASS_ADAPTER_PROPS:
                        if not filters or lower_camel_case(pass_property) in filters:
                            controller_result[lower_camel_case(pass_property)] = (
                                1
                                if await Bluetooth().get_device_property(
                                    obj_path=adapter_iface.path,
                                    interface=ADAPTER_IFACE,
                                    property_name=pass_property,
                                )
                                else 0
                            )
                            matched_filter = True

                    result[controller_friendly_name] = controller_result
                    if filters and not matched_filter:
                        if is_legacy:
                            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS[
                                "SDCERR_FAIL"
                            ]
                            result["InfoMsg"] = f"filters {filters} not matched"
                            resp.media = result
                            return
                        resp.status = falcon.HTTP_400
                        return
                else:
                    result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
                    device, device_props = await find_device(bus, device_uuid)
                    if not device:
                        if is_legacy:
                            result["InfoMsg"] = "Device not found"
                            resp.media = result
                            return
                        resp.status = falcon.HTTP_400
                        return
                    result.update(device_props)
                result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as exception:
            Bluetooth().log_exception(exception)
            result["InfoMsg"] = f"Error: {str(exception)}"

        resp.media = BluetoothRESTService.prepare_response_media(result, is_legacy)

    @staticmethod
    async def handle_put(
        req: falcon.asgi.Request,
        resp: falcon.asgi.Response,
        controller_name: str,
        device: str,
        is_legacy: bool = False,
    ) -> falcon.asgi.Response:
        """PUT handler"""
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "",
        }

        await Bluetooth().register_controller_callbacks()

        controller_friendly_name = (
            controller_pretty_name(controller_name)
            if controller_name
            else "controller0"
        )

        controller = await Bluetooth().get_remapped_controller(controller_friendly_name)

        device_uuid = uri_to_uuid(device) if device else None

        post_data = await req.get_media()
        bus, adapter_obj, get_controller_result = await get_controller_obj(controller)

        result.update(get_controller_result)

        if not adapter_obj:
            if not is_legacy:
                resp.status = falcon.HTTP_404
            resp.media = BluetoothRESTService.prepare_response_media(result, is_legacy)
            return

        controller_state = Bluetooth().get_controller_state(controller_friendly_name)

        try:
            adapter_interface = adapter_obj.get_interface(ADAPTER_IFACE)

            command = post_data["command"] if "command" in post_data else None
            if not device_uuid:
                # adapter-specific operation
                if command:
                    if command not in Bluetooth().adapter_commands:
                        if is_legacy:
                            result.update(
                                Bluetooth().result_parameter_not_one_of(
                                    "command", Bluetooth().adapter_commands
                                )
                            )
                            resp.media = result
                            return
                        resp.status = falcon.HTTP_400
                        return
                    else:
                        result.update(
                            await Bluetooth().execute_adapter_command(
                                bus,
                                command,
                                controller_friendly_name,
                                adapter_interface,
                                post_data,
                            )
                        )
                    resp.media = BluetoothRESTService.prepare_response_media(
                        result, is_legacy
                    )
                    return

                for prop in CACHED_ADAPTER_PROPS:
                    if prop in post_data:
                        controller_state.properties[prop] = post_data.get(prop)
                result.update(
                    await Bluetooth().set_adapter_properties(
                        adapter_interface,
                        controller_friendly_name,
                        post_data,
                    )
                )
            else:
                # device-specific operation
                if command and command not in Bluetooth().device_commands:
                    if is_legacy:
                        result.update(
                            Bluetooth().result_parameter_not_one_of(
                                "command", Bluetooth().device_commands
                            )
                        )
                        resp.media = result
                        return
                    resp.status = falcon.HTTP_400
                    return
                device, _ = await find_device(bus, device_uuid)
                if device is None:
                    result["InfoMsg"] = "Device not found"
                    if command:
                        # Forward device-specific commands on to plugins even if device
                        # is not found:
                        result.update(
                            await Bluetooth().execute_device_command(
                                bus, command, device_uuid, None, None, post_data
                            )
                        )
                    resp.media = BluetoothRESTService.prepare_response_media(
                        result, is_legacy
                    )
                    return

                device_obj = bus.get_proxy_object(
                    BLUEZ_SERVICE_NAME,
                    device,
                    await bus.introspect(BLUEZ_SERVICE_NAME, device),
                )
                device_interface = device_obj.get_interface(DEVICE_IFACE)

                if command:
                    result.update(
                        await Bluetooth().execute_device_command(
                            bus,
                            command,
                            device_uuid,
                            device_interface,
                            adapter_interface,
                            post_data,
                        )
                    )
                    resp.media = BluetoothRESTService.prepare_response_media(
                        result, is_legacy
                    )
                    return

                cached_device_properties = Bluetooth().get_device_properties(
                    controller_state, device_uuid
                )
                for prop in CACHED_DEVICE_PROPS:
                    if prop in post_data:
                        cached_device_properties[prop] = post_data.get(prop)
                result.update(
                    await Bluetooth().set_device_properties(
                        adapter_interface,
                        device_interface,
                        device_uuid,
                        post_data,
                    )
                )

        except Exception as exception:
            result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
            Bluetooth().log_exception(exception)
            result["InfoMsg"] = f"Error: {str(exception)}"

        resp.media = BluetoothRESTService.prepare_response_media(result, is_legacy)
