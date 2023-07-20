source ../global_settings

echo -e "\n========================="
echo "Bluetooth Get Connection Info (GetConnInfo)"

if [ -z "$BT_DEVICE" ]
then
    echo "Please invoke with Bluetooth device address set e.g. BT_DEVICE=xx:xx:xx:xx:xx:xx $0"
    exit
fi

echo -e "\nBluetooth Get Connection Info:\n"
${CURL_APP} --location --request PUT ${URL}/api/v2/bluetooth/${BT_CONTROLLER}/${BT_DEVICE} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data '{"command": "getConnInfo"}' \
    | ${JQ_APP}
echo -e '\n'

# Note reported RSSI may differ due to minimum RSSI difference to update device cached value logic.
echo -e "\nread Bluetooth state:\n"
${CURL_APP} --location --request GET ${URL}/api/v2/bluetooth/${BT_CONTROLLER}/${BT_DEVICE} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    | ${JQ_APP} | grep --color --context=99 -i rssi
echo -e '\n'
