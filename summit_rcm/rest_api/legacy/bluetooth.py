"""Module to support legacy Bluetooth requests"""


from summit_rcm.bluetooth.bt_rest_service import BluetoothRESTService


class BluetoothControllerLegacyResource:
    """
    Resource to handle legacy controller requests when no device which is just a wrapper around the
    common BluetoothRESTService request handler
    """

    async def on_get(self, req, resp, controller):
        """
        GET handler for the /bluetooth/{controller} endpoint
        """
        resp = await BluetoothRESTService.handle_get(
            req, resp, controller, None, is_legacy=True
        )

    async def on_put(self, req, resp, controller):
        """
        PUT handler for the /bluetooth/{controller} endpoint
        """
        resp = await BluetoothRESTService.handle_put(
            req, resp, controller, None, is_legacy=True
        )


class BluetoothDeviceLegacyResource:
    """
    Resource to handle legacy device requests which is just a wrapper around the common
    BluetoothRESTService request handler
    """

    async def on_get(self, req, resp, controller, device):
        """
        GET handler for the /bluetooth/{controller}/{device} endpoint
        """
        resp = await BluetoothRESTService.handle_get(
            req, resp, controller, device, is_legacy=True
        )

    async def on_put(self, req, resp, controller, device):
        """
        PUT handler for the /bluetooth/{controller}/{device} endpoint
        """
        resp = await BluetoothRESTService.handle_put(
            req, resp, controller, device, is_legacy=True
        )
