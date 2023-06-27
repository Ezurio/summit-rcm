#! /bin/bash

CONNECTION_NAME="${CONNECTION_NAME:-"PSK"}"
SSID="${SSID:-"SSID"}"
PSK="${PSK:-"password"}"
UUID="${UUID:-"9e08345f-3e9e-4a11-a556-0c476d291c11"}"

source ../global_settings

echo "========================="
echo "Create/replace PSK connection using explicit UUID"
echo "========================="
echo

echo "Connection Name (id): ${CONNECTION_NAME}"
echo "SSID: ${SSID}"
echo "PSK: ${PSK}"
echo "UUID: ${UUID}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/network/connections/uuid/${UUID} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data '{
        "connection": {
            "autoconnect": 1,
            "id": "'"${CONNECTION_NAME}"'",
            "interface-name": "wlan0",
            "type": "802-11-wireless"
        },
        "802-11-wireless": {
            "acs": 0,
            "frequency-dfs": 1,
            "hidden": 0,
            "mode": "infrastructure",
            "ssid": "'"${SSID}"'",
            "bgscan": "laird:5:-64:30"
        },
        "802-11-wireless-security": {
            "key-mgmt": "wpa-psk",
            "psk":  "'"${PSK}"'"
        }
    }' \
    -o >(${JQ_APP})

wait
