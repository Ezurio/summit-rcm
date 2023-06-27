source ../global_settings

VSP_TCP_PORT="${VSP_TCP_PORT:-1025}"

echo -e "\n========================="
echo "Bluetooth virtual serial port (gatt characteristics) disconnect"

if [ -z "$BT_DEVICE" ]
then
    echo "Please invoke with Bluetooth device address set e.g. BT_DEVICE=xx:xx:xx:xx:xx:xx $0"
    exit
fi

echo -e "\nclose vsp service port:\n"

${CURL_APP} --location --request PUT ${URL}/bluetooth/${BT_CONTROLLER}/${BT_DEVICE} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data '{
        "command": "gattDisconnect"
        }' \
    | ${JQ_APP}

echo -e "\ncheck VSP service ports:\n"
${CURL_APP} --location --request PUT ${URL}/bluetooth/${BT_CONTROLLER} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data '{
        "command": "gattList"
        }' \
    | ${JQ_APP}

echo -e "\nBluetooth disconnect:\n"
${CURL_APP} --location --request PUT ${URL}/bluetooth/${BT_CONTROLLER}/${BT_DEVICE} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data '{"connected": 0}' \
    | ${JQ_APP}
echo -e '\n'

echo -e "\nread Bluetooth state:\n"
${CURL_APP} --location --request GET ${URL}/bluetooth/${BT_CONTROLLER}/${BT_DEVICE} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    | ${JQ_APP} | grep --color --context=99 Connected
echo -e '\n'

