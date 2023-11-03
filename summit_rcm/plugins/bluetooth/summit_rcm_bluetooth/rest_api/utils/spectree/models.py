"""Module to hold SpecTree Models"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from summit_rcm.rest_api.utils.spectree.models import DefaultResponseModelLegacy
from summit_rcm_bluetooth.services.ble import (
    BLEWriteCharacteristicType,
    VSPSocketRxTypeEnum,
)


class BluetoothCommandEnum(str, Enum):
    """Enumeration of valid Bluetooth commands"""

    BLE_CONNECT = "bleConnect"
    BLE_DISCONNECT = "bleDisconnect"
    BLE_GATT = "bleGatt"
    BLE_START_SERVER = "bleStartServer"
    BLE_STOP_SERVER = "bleStopServer"
    BLE_SERVER_STATUS = "bleServerStatus"
    BLE_START_DISCOVERY = "bleStartDiscovery"
    BLE_STOP_DISCOVERY = "bleStopDiscovery"
    BLE_ENABLE_WEBSOCKETS = "bleEnableWebsockets"
    HID_CONNECT = "hidConnect"
    HID_DISCONNECT = "hidDisconnect"
    HID_LIST = "hidList"
    GATT_CONNECT = "gattConnect"
    GATT_DISCONNECT = "gattDisconnect"
    GATT_LIST = "gattList"
    GET_CONN_INFO = "getConnInfo"


class BluetoothGATTOperationEnum(str, Enum):
    """Enumeration of valid Bluetooth GATT operations"""

    BLE_GATT_READ = "read"
    BLE_GATT_WRITE = "write"
    BLE_GATT_NOTIFY = "notify"


class BluetoothDeviceModel(BaseModel):
    """Model for a Bluetooth device"""

    AutoConnect: Optional[int] = Field(description="Auto-connect state")
    AutoConnectAutoDisable: Optional[int] = Field(
        description="Auto-connect auto-disable"
    )
    Address: Optional[str] = Field(description="Device address")
    AddressType: Optional[str] = Field(description="Device address type")
    Name: Optional[str] = Field(description="Device name")
    Alias: Optional[str] = Field(description="Device alias")
    Paired: Optional[int] = Field(description="Paired state")
    Bonded: Optional[int] = Field(description="Bonded state")
    Trusted: Optional[int] = Field(description="Trusted state")
    Blocked: Optional[int] = Field(description="Blocked state")
    LegacyPairing: Optional[int] = Field(description="Legacy pairing state")
    RSSI: Optional[int] = Field(description="RSSI")
    Connected: Optional[int] = Field(description="Connected state")
    UUIDs: Optional[List[str]] = Field(description="List of UUIDs")
    Adapter: Optional[str] = Field(description="Adapter")
    ManufacturerData: Optional[Dict[str, Any]] = Field(description="Manufacturer data")
    ServiceData: Optional[Dict[str, Any]] = Field(description="Service data")
    ServicesResolved: Optional[int] = Field(description="Services resolved state")


class BluetoothConnectionModel(BaseModel):
    """Model for a Bluetooth connection (HID or GATT)"""

    device: str = Field(description="Device address")
    port: int = Field(description="Port")


class BluetoothControllerModel(BaseModel):
    """Model for the response to a request for Bluetooth controller information"""

    bluetoothDevices: Optional[List[BluetoothDeviceModel]] = Field(
        description="List of Bluetooth devices"
    )
    transportFilter: Optional[str] = Field(description="Transport filter")
    discovering: Optional[int] = Field(description="Discovering state")
    powered: Optional[int] = Field(description="Power state")
    discoverable: Optional[int] = Field(description="Discoverable state")


class BluetoothStateResponseModel(BaseModel):
    """Model for the response to a request for Bluetooth state"""

    __root__: Dict[str, BluetoothControllerModel]


class BluetoothStateResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for the response to a request for Bluetooth state (legacy)"""

    controller0: Optional[BluetoothControllerModel]


class BluetoothStateQueryModel(BaseModel):
    """Model for the query parameters for a request for Bluetooth state"""

    filter: Optional[str] = Field(
        description="Comma-separated list of filters to apply to the query"
    )


class BluetoothControlRequestModel(BaseModel):
    """Model for a request to control a Bluetooth controller"""

    command: Optional[BluetoothCommandEnum] = Field(description="Bluetooth command")
    powered: Optional[int] = Field(description="Power state")
    discovering: Optional[int] = Field(description="Discovering state")
    discoverable: Optional[int] = Field(description="Discoverable state")
    transportFilter: Optional[str] = Field(description="Transport filter")
    autoConnect: Optional[int] = Field(description="Auto-connect state")
    paired: Optional[int] = Field(description="Paired state")
    passkey: Optional[str] = Field(description="Passkey")
    connected: Optional[int] = Field(description="Connected state")
    purge: Optional[bool] = Field(description="Purge flag (for bleDisconnect command)")
    svcUuid: Optional[str] = Field(description="Service UUID (for bleGatt command)")
    chrUuid: Optional[str] = Field(
        description="Characteristic UUID (for bleGatt command)"
    )
    operation: Optional[BluetoothGATTOperationEnum] = Field(
        description="GATT operation (for bleGatt command)"
    )
    value: Optional[Any] = Field(
        description="Value (for bleGatt command with an operation of write)"
    )
    enable: Optional[bool] = Field(
        description="Enable flag (for bleGatt command with an operation of notify)"
    )
    tcpPort: Optional[int] = Field(description="TCP port (for VSP gattConnect command)")
    vspSvcUuid: Optional[str] = Field(
        description="VSP service UUID (for VSP gattConnect command)"
    )
    vspReadChrUuid: Optional[str] = Field(
        description="VSP read characteristic UUID (for VSP gattConnect command)"
    )
    vspWriteChrUuid: Optional[str] = Field(
        description="VSP write characteristic UUID (for VSP gattConnect command)"
    )
    vspWriteChrSize: Optional[int] = Field(
        description="VSP write characteristic size (for VSP gattConnect command)"
    )
    vspWriteChrType: Optional[BLEWriteCharacteristicType] = Field(
        description="VSP write characteristic type (for VSP gattConnect command)"
    )
    socketRxType: Optional[VSPSocketRxTypeEnum] = Field(
        description="Socket Rx type (for VSP gattConnect command)",
        default=VSPSocketRxTypeEnum.BLE_VSP_SOCKET_RX_TYPE_JSON,
    )


class BluetoothControlResponseModel(BaseModel):
    """Model for the response to a request to control a Bluetooth controller"""

    rssi: Optional[int] = Field(
        description="RSSI return value for the getConnInfo command"
    )
    tx_power: Optional[int] = Field(
        description="Tx power return value for the getConnInfo command"
    )
    max_tx_power: Optional[int] = Field(
        description="Max Tx power return value for the getConnInfo command"
    )
    HidConnections: Optional[List[BluetoothConnectionModel]] = Field(
        description="List of HID connections return value for the hidList command"
    )
    started: Optional[bool] = Field(
        description="Started return value for the bleServerStatus command"
    )
    port: Optional[int] = Field(
        description="Port return value for the bleServerStatus command"
    )
    GattConnections: Optional[List[BluetoothConnectionModel]] = Field(
        description="List of GATT connections return value for the gattList command"
    )


class BluetoothControlResponseModelLegacy(
    BluetoothControlResponseModel, DefaultResponseModelLegacy
):
    """Model for the response to a request to control a Bluetooth controller (legacy)"""
