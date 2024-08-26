##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

CONNECTION_NAME=WPA3-SAE

source ../global_settings

echo "WPA3 SAE"
echo ""
echo "========================="
echo "Create connection"
${CURL_APP} -s --header "Content-Type: application/json" \
    --request POST \
    ${URL}/connection \
    -b cookie -c cookie --insecure \
    --data '{
        "connection": {
            "autoconnect": 0,
            "id": "'"${CONNECTION_NAME}"'",
            "interface-name": "wlan0",
            "type": "802-11-wireless",
            "uuid": "",
            "zone": "trusted"
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
            "key-mgmt": "sae",
            "proto": "wpa3"
        }
    }'\
        | ${JQ_APP}

echo -e "\n"

