"""Init File to setup the Bluetooth Plugin"""
from syslog import syslog, LOG_ERR
import summit_rcm


async def get_legacy_routes():
    """Function to import and return bluetooth API Routes"""
    routes = {}
    try:
        from summit_rcm_bluetooth.services.bt import Bluetooth
        from summit_rcm_bluetooth.services.bt_ble import websockets_auth_by_header_token
        from summit_rcm_bluetooth.rest_api.legacy.bluetooth import (
            BluetoothControllerLegacyResource,
            BluetoothDeviceLegacyResource,
            BluetoothLegacyResource,
        )

        await Bluetooth().setup(summit_rcm.app)
        if websockets_auth_by_header_token:
            summit_rcm.SessionCheckingMiddleware().paths.append("bluetoothWebsocket/ws")
            Bluetooth().add_ws_route(
                ws_route="/bluetoothWebsocket/ws", is_legacy=True
            )
        summit_rcm.SessionCheckingMiddleware().paths.append("bluetooth")
        routes["/bluetooth"] = BluetoothLegacyResource()
        routes["/bluetooth/{controller}"] = BluetoothControllerLegacyResource()
        routes["/bluetooth/{controller}/{device}"] = BluetoothDeviceLegacyResource()
    except ImportError:
        pass
    except Exception as exception:
        syslog(LOG_ERR, f"Error Importing bluetooth legacy routes: {str(exception)}")
    return routes


async def get_v2_routes():
    """Function to import and return bluetooth API Routes"""
    routes = {}
    try:
        from summit_rcm_bluetooth.services.bt import Bluetooth
        from summit_rcm_bluetooth.services.bt_ble import websockets_auth_by_header_token
        from summit_rcm_bluetooth.rest_api.v2.bluetooth.bluetooth import (
            BluetoothControllerV2Resource,
            BluetoothDeviceV2Resource,
            BluetoothV2Resource,
        )

        await Bluetooth().setup(summit_rcm.app)
        if websockets_auth_by_header_token:
            summit_rcm.SessionCheckingMiddleware().paths.append("/api/v2/bluetooth/ws")
            Bluetooth().add_ws_route(
                ws_route="/api/v2/bluetooth/ws", is_legacy=False
            )
        summit_rcm.SessionCheckingMiddleware().paths.append("/api/v2/bluetooth")
        routes["/api/v2/bluetooth"] = BluetoothV2Resource()
        routes["/api/v2/bluetooth/{controller}"] = BluetoothControllerV2Resource()
        routes["/api/v2/bluetooth/{controller}/{device}"] = BluetoothDeviceV2Resource()
    except ImportError:
        pass
    except Exception as exception:
        syslog(LOG_ERR, f"Error Importing bluetooth v2 routes: {str(exception)}")
    return routes
