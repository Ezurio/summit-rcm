##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
CONNECTION_NAME=PEAP_WPA3_CA-cert

source ../global_settings

#known issue - only the last pahse2-autheap entry is retained.
echo ""
echo "PEAP WPA3 w/CA cert"
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
            "mode": "infrastructure",
            "ssid": "'"${SSID}"'"
        },
        "802-11-wireless-security": {
            "key-mgmt": "wpa-eap",
            "proto": "wpa3",
            "proactive-key-caching": 1
        },
        "802-1x": {
            "eap": "peap",
            "identity": "'"${WL_USERNAME}"'",
            "password": "'"${WL_PASSWORD}"'",
            "phase2-autheap": "gtc",
            "ca-cert": "'"${CA_CERT}"'",
            "client-cert": "None"
        }
    }'\
        | ${JQ_APP}

echo -e "\n"


