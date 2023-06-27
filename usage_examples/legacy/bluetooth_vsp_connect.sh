source ../global_settings

# Example UUIDs taken from Nordic nRF Connect SDK peripheral uart example project
VSP_SVC_UUID="${VSP_SVC_UUID:-6e400001-b5a3-f393-e0a9-e50e24dcca9e}"
VSP_READ_CHR_UUID="${VSP_READ_CHR_UUID:-6e400003-b5a3-f393-e0a9-e50e24dcca9e}"
VSP_WRITE_CHR_UUID="${VSP_WRITE_CHR_UUID:-6e400002-b5a3-f393-e0a9-e50e24dcca9e}"
# tcpPort may be in the range 1025 to 49151
VSP_TCP_PORT="${VSP_TCP_PORT:-1025}"
# socketRxType may be JSON or raw
VSP_SOCKET_RX_TYPE="JSON"

echo -e "\n========================="
echo "Bluetooth virtual serial port (gatt characteristics) connect"

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
    | ${JQ_APP} | grep --color --context=99 Connected
echo -e '\n'

echo -e "\nShort delay to allow VSP service to discover...\n"
sleep 1

echo -e "\nread Bluetooth state:\n"
${CURL_APP} --location --request GET ${URL}/bluetooth/${BT_CONTROLLER}/${BT_DEVICE} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    | ${JQ_APP} | grep --color --context=99 ServicesResolved
echo -e '\n'

echo -e "\nopen vsp port ${VSP_TCP_PORT}:\n"

${CURL_APP} --location --request PUT ${URL}/bluetooth/${BT_CONTROLLER}/${BT_DEVICE} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data '{
        "command": "gattConnect",
        "tcpPort": "'"${VSP_TCP_PORT}"'",
        "vspSvcUuid": "'"${VSP_SVC_UUID}"'",
        "vspReadChrUuid": "'"${VSP_READ_CHR_UUID}"'",
        "vspWriteChrUuid": "'"${VSP_WRITE_CHR_UUID}"'",
        "socketRxType": "'"${VSP_SOCKET_RX_TYPE}"'"
        }' \
    | ${JQ_APP}

echo -e "\n\ncheck VSP service ports:\n"
${CURL_APP} --location --request PUT ${URL}/bluetooth/${BT_CONTROLLER} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data '{
        "command": "gattList"
        }' \
    | ${JQ_APP}

echo -e "\n\nsend data to port:\n"
(while true; do echo "test data"; sleep 5; done) | nc ${IPADDR} ${VSP_TCP_PORT}

