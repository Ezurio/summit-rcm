#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""Module to hold SpecTree Models"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import Field
from summit_rcm.rest_api.utils.spectree.models import (
    DefaultResponseModelLegacy,
    BaseModel,
    RootModel,
)
from summit_rcm_bluetooth.services.ble import (
    BLEWriteCharacteristicType,
    BluetoothPairingIOCapability,
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

    AutoConnect: Optional[int] = Field(description="Auto-connect state", default=None)
    AutoConnectAutoDisable: Optional[int] = Field(
        description="Auto-connect auto-disable", default=None
    )
    Address: Optional[str] = Field(description="Device address", default=None)
    AddressType: Optional[str] = Field(description="Device address type", default=None)
    Name: Optional[str] = Field(description="Device name", default=None)
    Alias: Optional[str] = Field(description="Device alias", default=None)
    Paired: Optional[int] = Field(description="Paired state", default=None)
    Bonded: Optional[int] = Field(description="Bonded state", default=None)
    Trusted: Optional[int] = Field(description="Trusted state", default=None)
    Blocked: Optional[int] = Field(description="Blocked state", default=None)
    LegacyPairing: Optional[int] = Field(
        description="Legacy pairing state", default=None
    )
    RSSI: Optional[int] = Field(description="RSSI", default=None)
    Connected: Optional[int] = Field(description="Connected state", default=None)
    UUIDs: Optional[List[str]] = Field(description="List of UUIDs", default=None)
    Adapter: Optional[str] = Field(description="Adapter", default=None)
    ManufacturerData: Optional[Dict[str, Any]] = Field(
        description="Manufacturer data", default=None
    )
    ServiceData: Optional[Dict[str, Any]] = Field(
        description="Service data", default=None
    )
    ServicesResolved: Optional[int] = Field(
        description="Services resolved state", default=None
    )


class BluetoothConnectionModel(BaseModel):
    """Model for a Bluetooth connection (HID or GATT)"""

    device: str = Field(description="Device address")
    port: int = Field(description="Port")


class BluetoothControllerModel(BaseModel):
    """Model for the response to a request for Bluetooth controller information"""

    bluetoothDevices: Optional[List[BluetoothDeviceModel]] = Field(
        description="List of Bluetooth devices", default=None
    )
    RSSI: Optional[int] = Field(description="RSSI Discovery filter", default=None)
    Transport: Optional[str] = Field(description="Transport Discovery filter", default=None)
    Pattern: Optional[str] = Field(description="Pattern Discovery filter", default=None)
    discovering: Optional[int] = Field(description="Discovering state", default=None)
    powered: Optional[int] = Field(description="Power state", default=None)
    discoverable: Optional[int] = Field(description="Discoverable state", default=None)


class BluetoothStateResponseModel(RootModel):
    """Model for the response to a request for Bluetooth state"""

    root: Dict[str, BluetoothControllerModel]


class BluetoothStateResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for the response to a request for Bluetooth state (legacy)"""

    controller0: Optional[BluetoothControllerModel] = None


class BluetoothStateQueryModel(BaseModel):
    """Model for the query parameters for a request for Bluetooth state"""

    filter: Optional[str] = Field(
        description="Comma-separated list of filters to apply to the query",
        default=None,
    )


class BluetoothControlRequestModel(BaseModel):
    """Model for a request to control a Bluetooth controller"""

    command: Optional[BluetoothCommandEnum] = Field(
        description="Bluetooth command", default=None
    )
    powered: Optional[int] = Field(description="Power state", default=None)
    discovering: Optional[int] = Field(description="Discovering state", default=None)
    discoverable: Optional[int] = Field(description="Discoverable state", default=None)
    RSSI: Optional[int] = Field(description="RSSI Discovery filter", default=None)
    Transport: Optional[str] = Field(description="Transport Discovery filter", default=None)
    Pattern: Optional[str] = Field(description="Pattern Discovery filter", default=None)
    autoConnect: Optional[int] = Field(description="Auto-connect state", default=None)
    paired: Optional[int] = Field(description="Paired state", default=None)
    pairingIoCapability: Optional[BluetoothPairingIOCapability] = Field(
        description=(
            "Optional BlueZ pairing agent IO capability to register before a paired or "
            "connected request. Defaults to NoInputNoOutput when omitted."
        ),
        default=None,
    )
    passkey: Optional[str] = Field(description="Passkey", default=None)
    connected: Optional[int] = Field(description="Connected state", default=None)
    purge: Optional[bool] = Field(
        description="Purge flag (for bleDisconnect command)", default=None
    )
    svcUuid: Optional[str] = Field(
        description="Service UUID (for bleGatt command)", default=None
    )
    chrUuid: Optional[str] = Field(
        description="Characteristic UUID (for bleGatt command)", default=None
    )
    operation: Optional[BluetoothGATTOperationEnum] = Field(
        description="GATT operation (for bleGatt command)", default=None
    )
    value: Optional[Any] = Field(
        description="Value (for bleGatt command with an operation of write)",
        default=None,
    )
    enable: Optional[bool] = Field(
        description="Enable flag (for bleGatt command with an operation of notify)",
        default=None,
    )
    tcpPort: Optional[int] = Field(
        description="TCP port (for VSP gattConnect command)", default=None
    )
    vspSvcUuid: Optional[str] = Field(
        description="VSP service UUID (for VSP gattConnect command)", default=None
    )
    vspReadChrUuid: Optional[str] = Field(
        description="VSP read characteristic UUID (for VSP gattConnect command)",
        default=None,
    )
    vspWriteChrUuid: Optional[str] = Field(
        description="VSP write characteristic UUID (for VSP gattConnect command)",
        default=None,
    )
    vspWriteChrSize: Optional[int] = Field(
        description="VSP write characteristic size (for VSP gattConnect command)",
        default=None,
    )
    vspWriteChrType: Optional[BLEWriteCharacteristicType] = Field(
        description="VSP write characteristic type (for VSP gattConnect command)",
        default=None,
    )
    socketRxType: Optional[VSPSocketRxTypeEnum] = Field(
        description="Socket Rx type (for VSP gattConnect command)",
        default=VSPSocketRxTypeEnum.BLE_VSP_SOCKET_RX_TYPE_JSON,
    )


class BluetoothControlResponseModel(BaseModel):
    """Model for the response to a request to control a Bluetooth controller"""

    rssi: Optional[int] = Field(
        description="RSSI return value for the getConnInfo command", default=None
    )
    tx_power: Optional[int] = Field(
        description="Tx power return value for the getConnInfo command", default=None
    )
    max_tx_power: Optional[int] = Field(
        description="Max Tx power return value for the getConnInfo command",
        default=None,
    )
    HidConnections: Optional[List[BluetoothConnectionModel]] = Field(
        description="List of HID connections return value for the hidList command",
        default=None,
    )
    started: Optional[bool] = Field(
        description="Started return value for the bleServerStatus command", default=None
    )
    port: Optional[int] = Field(
        description="Port return value for the bleServerStatus command", default=None
    )
    GattConnections: Optional[List[BluetoothConnectionModel]] = Field(
        description="List of GATT connections return value for the gattList command",
        default=None,
    )


class BluetoothControlResponseModelLegacy(
    BluetoothControlResponseModel, DefaultResponseModelLegacy
):
    """Model for the response to a request to control a Bluetooth controller (legacy)"""
