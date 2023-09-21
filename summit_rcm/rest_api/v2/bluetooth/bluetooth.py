"""Module to support v2 Bluetooth requests"""


from summit_rcm.bluetooth.bt_rest_service import BluetoothRESTService


class BluetoothV2Resource:
    """
    Resource to handle v2 controller requests when no device or controller is specified which is
    just a wrapper around the common BluetoothRESTService request handler
    """

    async def on_get(self, req, resp):
        """
        GET handler for the /bluetooth endpoint
        """
        resp = await BluetoothRESTService.handle_get(
            req, resp, None, None, is_legacy=False
        )

    async def on_put(self, req, resp):
        """
        PUT handler for the /bluetooth endpoint
        """
        resp = await BluetoothRESTService.handle_put(
            req, resp, None, None, is_legacy=False
        )


class BluetoothControllerV2Resource:
    """
    Resource to handle v2 controller requests when no device is specified which is just a wrapper
    around the common BluetoothRESTService request handler
    """

    async def on_get(self, req, resp, controller):
        """
        GET handler for the /bluetooth/{controller} endpoint
        """
        resp = await BluetoothRESTService.handle_get(
            req, resp, controller, None, is_legacy=False
        )

    async def on_put(self, req, resp, controller):
        """
        PUT handler for the /bluetooth/{controller} endpoint
        """
        resp = await BluetoothRESTService.handle_put(
            req, resp, controller, None, is_legacy=False
        )


class BluetoothDeviceV2Resource:
    """
    Resource to handle v2 device requests which is just a wrapper around the common
    BluetoothRESTService request handler
    """

    async def on_get(self, req, resp, controller, device):
        """
        GET handler for the /bluetooth/{controller}/{device} endpoint
        """
        resp = await BluetoothRESTService.handle_get(
            req, resp, controller, device, is_legacy=False
        )

    async def on_put(self, req, resp, controller, device):
        """
        PUT handler for the /bluetooth/{controller}/{device} endpoint
        """
        resp = await BluetoothRESTService.handle_put(
            req, resp, controller, device, is_legacy=False
        )
