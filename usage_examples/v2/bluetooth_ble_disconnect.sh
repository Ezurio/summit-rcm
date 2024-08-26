##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings

echo -e "\n========================="
echo "Bluetooth ble disconnect"

if [ -z "$BT_DEVICE" ]
then
    echo "Please invoke with Bluetooth device address set e.g. BT_DEVICE=xx:xx:xx:xx:xx:xx $0"
    exit
fi

echo -e "\nBluetooth disconnect:\n"
${CURL_APP} --location --request PUT ${URL}/api/v2/bluetooth/${BT_CONTROLLER}/${BT_DEVICE} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data '{"command": "bleDisconnect"}' \
    | ${JQ_APP}
echo -e '\n'

echo -e "\nread Bluetooth state:\n"
${CURL_APP} --location --request GET ${URL}/api/v2/bluetooth/${BT_CONTROLLER}/${BT_DEVICE} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    | ${JQ_APP} | grep --color --context=99 Connected
echo -e '\n'

