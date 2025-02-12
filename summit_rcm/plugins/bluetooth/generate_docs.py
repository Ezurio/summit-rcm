#!/usr/bin/python
#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2025 Ezurio LLC.
#
"""
Generate the OpenAPI spec for the Summit RCM REST API for the Bluetooth plugin
"""


def generate_docs():
    """
    Generate the OpenAPI spec for the Summit RCM REST API for the Bluetooth plugin. This function is
    called duriong the build process to generate the OpenAPI spec for the Bluetooth plugin.
    """
    from summit_rcm.rest_api.utils.spectree.generate_api_spec import generate_api_spec

    routes = {}

    try:
        from summit_rcm_bluetooth.rest_api.legacy.bluetooth import (
            BluetoothControllerLegacyResource,
            BluetoothDeviceLegacyResource,
            BluetoothLegacyResource,
        )

        routes["/bluetooth"] = BluetoothLegacyResource
        routes["/bluetooth/{controller}"] = BluetoothControllerLegacyResource
        routes["/bluetooth/{controller}/{device}"] = BluetoothDeviceLegacyResource
    except ImportError:
        pass

    try:
        from summit_rcm_bluetooth.rest_api.v2.bluetooth.bluetooth import (
            BluetoothControllerV2Resource,
            BluetoothDeviceV2Resource,
            BluetoothV2Resource,
        )

        routes["/api/v2/bluetooth"] = BluetoothV2Resource
        routes["/api/v2/bluetooth/{controller}"] = BluetoothControllerV2Resource
        routes["/api/v2/bluetooth/{controller}/{device}"] = BluetoothDeviceV2Resource
    except ImportError:
        pass

    try:
        from summit_rcm_bluetooth.services.bt_ble_websocket import (
            BluetoothWebSocketResource,
        )

        routes["/bluetoothWebsocket/ws"] = BluetoothWebSocketResource
        routes["/api/v2/bluetooth/ws"] = BluetoothWebSocketResource
    except ImportError:
        pass

    generate_api_spec(routes)


if __name__ == "__main__":
    generate_docs()
