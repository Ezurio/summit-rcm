##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings

# tcpPort may be in the range 1025 to 49151
HID_TCP_PORT="${HID_TCP_PORT:-1025}"

echo -e "\n========================="
echo "Bluetooth hid barcode scanner connect"

if [ -z "$BT_DEVICE" ]
then
    echo "Please invoke with Bluetooth device address set e.g. BT_DEVICE=xx:xx:xx:xx:xx:xx $0"
    exit
fi

echo -e "\nBluetooth connect:\n"
${CURL_APP} --location --request PUT ${URL}/bluetooth/${BT_CONTROLLER}/${BT_DEVICE} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data '{"connected": 1}' \
    | ${JQ_APP}
echo -e '\n'

echo -e "\nread Bluetooth state:\n"
${CURL_APP} --location --request GET ${URL}/bluetooth/${BT_CONTROLLER}/${BT_DEVICE} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    | ${JQ_APP} | grep --context=99 --color Connected
echo -e '\n'

echo -e "\nShort delay to allow HID service to discover and open...\n"
sleep 1

echo -e "\nopen vsp port ${HID_TCP_PORT}:\n"

${CURL_APP} --location --request PUT ${URL}/bluetooth/${BT_CONTROLLER}/${BT_DEVICE} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data '{
        "command": "hidConnect",
        "tcpPort": "'"${HID_TCP_PORT}"'"
        }' \
    | ${JQ_APP}

echo -e "\n\ncheck HID service ports:\n"
${CURL_APP} --location --request PUT ${URL}/bluetooth/${BT_CONTROLLER} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data '{
        "command": "hidList"
        }' \
    | ${JQ_APP}

echo -e "\n\nconnecting to TCP port - please scan a barcode and confirm result:\n"
nc ${IPADDR} ${HID_TCP_PORT}

