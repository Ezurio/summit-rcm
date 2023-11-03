"""Module to support v2 Bluetooth requests"""

from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm_bluetooth.services.bt_rest_service import BluetoothRESTService

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        BadRequestErrorResponseModel,
        UnauthorizedErrorResponseModel,
        NotFoundErrorResponseModel,
        InternalServerErrorResponseModel,
    )
    from summit_rcm_bluetooth.rest_api.utils.spectree.models import (
        BluetoothStateResponseModel,
        BluetoothStateQueryModel,
        BluetoothControlRequestModel,
        BluetoothControlResponseModel,
    )
    from summit_rcm_bluetooth.rest_api.utils.spectree.tags import bluetooth_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    BadRequestErrorResponseModel = None
    UnauthorizedErrorResponseModel = None
    NotFoundErrorResponseModel = None
    InternalServerErrorResponseModel = None
    BluetoothStateResponseModel = None
    BluetoothStateQueryModel = None
    BluetoothControlRequestModel = None
    BluetoothControlResponseModel = None
    bluetooth_tag = None


spec = SpectreeService()


class BluetoothV2Resource:
    """
    Resource to handle v2 controller requests when no device or controller is specified which is
    just a wrapper around the common BluetoothRESTService request handler
    """

    @spec.validate(
        query=BluetoothStateQueryModel,
        resp=Response(
            HTTP_200=BluetoothStateResponseModel,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[bluetooth_tag],
    )
    async def on_get(self, req, resp):
        """
        Retrieve the state of all Bluetooth controllers and devices
        """
        resp = await BluetoothRESTService.handle_get(
            req, resp, None, None, is_legacy=False
        )

    @spec.validate(
        json=BluetoothControlRequestModel,
        resp=Response(
            HTTP_200=BluetoothControlResponseModel,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[bluetooth_tag],
    )
    async def on_put(self, req, resp):
        """
        Control and configure the default (controller0) Bluetooth controller

        This endpoint is very versatile and can be used to interact with the Bluetooth subsystem in
        many ways. It can be used to:
        <ul>
        <li>Enable or disable power to the Bluetooth controller</li>
        <li>Initiate a scan for nearby devices</li>
        <li>Configure the Bluetooth controller to be discoverable</li>
        <li>Configure a device transport filter</li>
        <li>Connect/disconnect from a peripheral device</li>
        <li>Pair/unpair with a peripheral device</li>
        <li>Enable/disable websockets for BLE information</li>
        <li>Issue specific commands</li>
        </ul>

        Supported commands:
        <ul>
        <li><code>bleConnect</code>: Connect to a BLE peripheral device</li>
        <li><code>bleDisconnect</code>: Disconnect from a BLE peripheral device</li>
        <li><code>bleGatt</code>: Issue a GATT command to a BLE peripheral device (read, write, notify)</li>
        <li><code>bleStartServer</code>: Start the BLE GATT server</li>
        <li><code>bleStopServer</code>: Stop the BLE GATT server</li>
        <li><code>bleServerStatus</code>: Get the status of the BLE GATT server</li>
        <li><code>bleStartDiscovery</code>: Start BLE discovery</li>
        <li><code>bleStopDiscovery</code>: Stop BLE discovery</li>
        <li><code>bleEnableWebsockets</code>: Enable websockets for BLE information</li>
        <li><code>hidConnect</code>: Connect to a HID peripheral device</li>
        <li><code>hidDisconnect</code>: Disconnect from a HID peripheral device</li>
        <li><code>hidList</code>: List HID devices</li>
        <li><code>gattConnect</code>: Connect to a GATT peripheral device (VSP)</li>
        <li><code>gattDisconnect</code>: Disconnect from a GATT peripheral device (VSP)</li>
        <li><code>gattList</code>: List GATT devices (VSP)</li>
        <li><code>getConnInfo</code>: Get connection information for a specific device</li>
        </ul>
        """
        resp = await BluetoothRESTService.handle_put(
            req, resp, None, None, is_legacy=False
        )


class BluetoothControllerV2Resource:
    """
    Resource to handle v2 controller requests when no device is specified which is just a wrapper
    around the common BluetoothRESTService request handler
    """

    @spec.validate(
        query=BluetoothStateQueryModel,
        resp=Response(
            HTTP_200=BluetoothStateResponseModel,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        path_parameter_descriptions={
            "controller": "The Bluetooth controller to interact with",
        },
        security=SpectreeService().security,
        tags=[bluetooth_tag],
    )
    async def on_get(self, req, resp, controller):
        """
        Retrieve the state of a specific Bluetooth controller and its devices
        """
        resp = await BluetoothRESTService.handle_get(
            req, resp, controller, None, is_legacy=False
        )

    @spec.validate(
        json=BluetoothControlRequestModel,
        resp=Response(
            HTTP_200=BluetoothControlResponseModel,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        path_parameter_descriptions={
            "controller": "The Bluetooth controller to interact with",
        },
        security=SpectreeService().security,
        tags=[bluetooth_tag],
    )
    async def on_put(self, req, resp, controller):
        """
        Control and configure a specific Bluetooth controller

        This endpoint is very versatile and can be used to interact with the Bluetooth subsystem in
        many ways. It can be used to:
        <ul>
        <li>Enable or disable power to the Bluetooth controller</li>
        <li>Initiate a scan for nearby devices</li>
        <li>Configure the Bluetooth controller to be discoverable</li>
        <li>Configure a device transport filter</li>
        <li>Connect/disconnect from a peripheral device</li>
        <li>Pair/unpair with a peripheral device</li>
        <li>Enable/disable websockets for BLE information</li>
        <li>Issue specific commands</li>
        </ul>

        Supported commands:
        <ul>
        <li><code>bleConnect</code>: Connect to a BLE peripheral device</li>
        <li><code>bleDisconnect</code>: Disconnect from a BLE peripheral device</li>
        <li><code>bleGatt</code>: Issue a GATT command to a BLE peripheral device (read, write, notify)</li>
        <li><code>bleStartServer</code>: Start the BLE GATT server</li>
        <li><code>bleStopServer</code>: Stop the BLE GATT server</li>
        <li><code>bleServerStatus</code>: Get the status of the BLE GATT server</li>
        <li><code>bleStartDiscovery</code>: Start BLE discovery</li>
        <li><code>bleStopDiscovery</code>: Stop BLE discovery</li>
        <li><code>bleEnableWebsockets</code>: Enable websockets for BLE information</li>
        <li><code>hidConnect</code>: Connect to a HID peripheral device</li>
        <li><code>hidDisconnect</code>: Disconnect from a HID peripheral device</li>
        <li><code>hidList</code>: List HID devices</li>
        <li><code>gattConnect</code>: Connect to a GATT peripheral device (VSP)</li>
        <li><code>gattDisconnect</code>: Disconnect from a GATT peripheral device (VSP)</li>
        <li><code>gattList</code>: List GATT devices (VSP)</li>
        <li><code>getConnInfo</code>: Get connection information for a specific device</li>
        </ul>
        """
        resp = await BluetoothRESTService.handle_put(
            req, resp, controller, None, is_legacy=False
        )


class BluetoothDeviceV2Resource:
    """
    Resource to handle v2 device requests which is just a wrapper around the common
    BluetoothRESTService request handler
    """

    @spec.validate(
        query=BluetoothStateQueryModel,
        resp=Response(
            HTTP_200=BluetoothStateResponseModel,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        path_parameter_descriptions={
            "controller": "The Bluetooth controller to interact with",
            "device": "The address of the Bluetooth device to interact with",
        },
        security=SpectreeService().security,
        tags=[bluetooth_tag],
    )
    async def on_get(self, req, resp, controller, device):
        """
        Retrieve the state of a specific Bluetooth controller and device
        """
        resp = await BluetoothRESTService.handle_get(
            req, resp, controller, device, is_legacy=False
        )

    @spec.validate(
        json=BluetoothControlRequestModel,
        resp=Response(
            HTTP_200=BluetoothControlResponseModel,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        path_parameter_descriptions={
            "controller": "The Bluetooth controller to interact with",
            "device": "The address of the Bluetooth device to interact with",
        },
        security=SpectreeService().security,
        tags=[bluetooth_tag],
    )
    async def on_put(self, req, resp, controller, device):
        """
        Control and configure a specific device connected to a specific Bluetooth controller

        This endpoint is very versatile and can be used to interact with the Bluetooth subsystem in
        many ways. It can be used to:
        <ul>
        <li>Enable or disable power to the Bluetooth controller</li>
        <li>Initiate a scan for nearby devices</li>
        <li>Configure the Bluetooth controller to be discoverable</li>
        <li>Configure a device transport filter</li>
        <li>Connect/disconnect from a peripheral device</li>
        <li>Pair/unpair with a peripheral device</li>
        <li>Enable/disable websockets for BLE information</li>
        <li>Issue specific commands</li>
        </ul>

        Supported commands:
        <ul>
        <li><code>bleConnect</code>: Connect to a BLE peripheral device</li>
        <li><code>bleDisconnect</code>: Disconnect from a BLE peripheral device</li>
        <li><code>bleGatt</code>: Issue a GATT command to a BLE peripheral device (read, write, notify)</li>
        <li><code>bleStartServer</code>: Start the BLE GATT server</li>
        <li><code>bleStopServer</code>: Stop the BLE GATT server</li>
        <li><code>bleServerStatus</code>: Get the status of the BLE GATT server</li>
        <li><code>bleStartDiscovery</code>: Start BLE discovery</li>
        <li><code>bleStopDiscovery</code>: Stop BLE discovery</li>
        <li><code>bleEnableWebsockets</code>: Enable websockets for BLE information</li>
        <li><code>hidConnect</code>: Connect to a HID peripheral device</li>
        <li><code>hidDisconnect</code>: Disconnect from a HID peripheral device</li>
        <li><code>hidList</code>: List HID devices</li>
        <li><code>gattConnect</code>: Connect to a GATT peripheral device (VSP)</li>
        <li><code>gattDisconnect</code>: Disconnect from a GATT peripheral device (VSP)</li>
        <li><code>gattList</code>: List GATT devices (VSP)</li>
        <li><code>getConnInfo</code>: Get connection information for a specific device</li>
        </ul>
        """
        resp = await BluetoothRESTService.handle_put(
            req, resp, controller, device, is_legacy=False
        )
