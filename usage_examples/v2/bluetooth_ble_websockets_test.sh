#!/bin/bash
if [ ! -z "$1" ]
then
    export IPADDR=$1
fi

SUMMIT_RCM_PASSWORD=summit ./login_post.sh
./bluetooth_ble_enable_websockets.sh &
cat cookie
echo "Try Postman to wss://${IPADDR}/api/v2/bluetooth/ws"
echo " (or ws://..., should redirect)"
echo "Add headers key 'Cookie', value 'session_id=[from_cookie]'"
sleep 10
./bluetooth_scan.sh
BT_DEVICE=E0:13:7D:9D:2E:45  ./bluetooth_ble_connect.sh
BT_DEVICE=E0:13:7D:9D:2E:45  ./bluetooth_ble_disconnect.sh
BT_DEVICE=E0:13:7D:9D:2E:45  ./bluetooth_ble_connect.sh
BT_DEVICE=E0:13:7D:9D:2E:45  ./bluetooth_ble_gatt_notify.sh
BT_DEVICE=E0:13:7D:9D:2E:45 GATT_DATA=3132330D0A ./bluetooth_ble_gatt_write.sh
