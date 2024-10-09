#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

CONNECTION_NAME="${CONNECTION_NAME:-"PSK"}"
NEW_CONNECTION_NAME="${NEW_CONNECTION_NAME:-"${CONNECTION_NAME}"}"
SSID="${SSID:-"SSID"}"
PSK="${PSK:-"password"}"

source ../global_settings

echo "========================="
echo "Create/replace PSK connection using connection name (id)"
echo "========================="
echo

echo "Connection Name (id): ${CONNECTION_NAME}"
echo "New Connection Name (id): ${NEW_CONNECTION_NAME}"
echo "SSID: ${SSID}"
echo "PSK: ${PSK}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/network/connections/id/${CONNECTION_NAME} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data '{
        "connection": {
            "autoconnect": 1,
            "id": "'"${NEW_CONNECTION_NAME}"'",
            "interface-name": "wlan0",
            "type": "802-11-wireless"
        },
        "802-11-wireless": {
            "acs": 0,
            "frequency-dfs": 1,
            "hidden": 0,
            "mode": "infrastructure",
            "ssid": "'"${SSID}"'",
            "bgscan": "summit:5:-64:30"
        },
        "802-11-wireless-security": {
            "key-mgmt": "wpa-psk",
            "psk":  "'"${PSK}"'"
        }
    }' \
    -o >(${JQ_APP})

wait
