##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
CONNECTION_NAME=EAP_TLS_CA_CERT

source ../global_settings

echo "EAP TLS CA cert"
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
            "bgscan": "summit:5:-64:30"
        },
        "802-11-wireless-security": {
            "key-mgmt": "wpa-eap",
            "proto": "rsn",
            "pairwise": "ccmp",
            "proactive-key-caching": 1
        },
        "802-1x": {
            "auth-timeout": 0,
            "eap": "tls",
            "private-key-password": "'"${PRIVATE_KEY_PASSWORD}"'",
            "private-key": "'"${PRIVATE_KEY}"'",
            "identity": "'"${WL_USERNAME}"'",
            "password": "'"${WL_PASSWORD}"'",
            "client-cert": "None",
            "ca-cert": "'"${CA_CERT}"'"
        }
    }'\
        | ${JQ_APP}

echo -e "\n"


