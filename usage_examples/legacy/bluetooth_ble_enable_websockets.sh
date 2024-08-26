##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings

echo -e "\n========================="
echo "Bluetooth ble api websockets"

echo -e "\nenable websockets:\n"

${CURL_APP} --location --request PUT ${URL}/bluetooth/${BT_CONTROLLER} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data '{
        "command": "bleEnableWebsockets"
        }' \
    | ${JQ_APP}

echo -e "\n\nopen connection to listen:\n"
curl --include --header "Connection: Upgrade" --header "Upgrade: websocket" --header "Host: ${IPADDR}" --header "Origin: http://${IPADDR}/bluetoothWebsocket/ws" --header "Sec-WebSocket-Key: 1243SGVsbG8sIHdvcmxkIQ==" --header "Sec-WebSocket-Version: 13" --request GET https://${IPADDR}/bluetoothWebsocket/ws --insecure -b cookie -c cookie --output -
