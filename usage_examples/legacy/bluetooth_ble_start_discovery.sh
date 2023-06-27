source ../global_settings

echo -e "\n========================="
echo "Bluetooth ble start discovery"

${CURL_APP} --location --request PUT ${URL}/bluetooth/${BT_CONTROLLER} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data '{
        "command": "bleStartDiscovery"
        }' \
    | ${JQ_APP}

