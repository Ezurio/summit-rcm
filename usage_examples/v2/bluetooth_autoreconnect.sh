source ../global_settings

BT_AUTOCONNECT="${BT_AUTOCONNECT:-1}"

echo -e "\n========================="
echo "Bluetooth auto reconnect"

if [ -z "$BT_DEVICE" ]
then
    echo "Please invoke with Bluetooth device address set e.g. BT_DEVICE=xx:xx:xx:xx:xx:xx $0"
    echo "Optional parameter is BT_AUTOCONNECT=[0|1], default 1."
    exit
fi

echo -e "\nset trusted and autoConnect:\n"
${CURL_APP} --location --request PUT ${URL}/api/v2/bluetooth/${BT_CONTROLLER}/${BT_DEVICE} \
    --header "Content-Type: application/json" \
    -b cookie --insecure\
    --data "{\"autoConnect\": ${BT_AUTOCONNECT}}" \
    | ${JQ_APP}
echo -e '\n'

echo -e "\nread state:\n"
${CURL_APP} --location --request GET ${URL}/api/v2/bluetooth/${BT_CONTROLLER}/${BT_DEVICE} \
    --header "Content-Type: application/json" \
    -b cookie --insecure\
    | ${JQ_APP}
echo -e '\n'
