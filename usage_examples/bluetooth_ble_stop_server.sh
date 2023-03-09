source global_settings

echo -e "\n========================="
echo "Bluetooth ble server stop"

${CURL_APP} --location --request PUT ${URL}/bluetooth/${BT_CONTROLLER} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data '{
        "command": "bleStopServer"
        }' \
    | ${JQ_APP}

