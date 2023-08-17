#! /bin/bash

SSID="${SSID:-"SSID"}"
CONNECTION_NAME="${CONNECTION_NAME:-"connection-id"}"

source ../global_settings

echo "========================="
echo "Update connection's SSID using connection name (id)"
echo "========================="
echo

echo "SSID: ${SSID}"
echo "Connection Name (id): ${CONNECTION_NAME}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PATCH ${URL}/api/v2/network/connections/id/${CONNECTION_NAME} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data '{
        "802-11-wireless": {
            "ssid": "'"${SSID}"'"
        }
    }' \
    -o >(${JQ_APP})

wait
