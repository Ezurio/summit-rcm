source ../global_settings

echo -e "\n========================="
echo "Bluetooth ble connect"

if [ -z "$BT_DEVICE" ]
then
    echo "Please invoke with Bluetooth device address set e.g. BT_DEVICE=xx:xx:xx:xx:xx:xx $0"
    exit
fi

echo -e "\nBluetooth connect:\n"
${CURL_APP} --location --request PUT ${URL}/bluetooth/${BT_CONTROLLER}/${BT_DEVICE} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data '{"command": "bleConnect"}' \
    | ${JQ_APP}
echo -e '\n'

echo -e "\nread Bluetooth state:\n"
${CURL_APP} --location --request GET ${URL}/bluetooth/${BT_CONTROLLER}/${BT_DEVICE} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    | ${JQ_APP} | grep --color --context=99 Connected
echo -e '\n'

echo -e "\nShort delay to allow services to discover...\n"
sleep 1

echo -e "\nread Bluetooth state:\n"
${CURL_APP} --location --request GET ${URL}/bluetooth/${BT_CONTROLLER}/${BT_DEVICE} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    | ${JQ_APP} | grep --color --context=99 ServicesResolved
echo -e '\n'

