##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
CONNECTION_NAME=EAP_TTLS_CA_CERT

source ../global_settings

#known issue - only the last pahse2-autheap entry is retained.
echo "EAP TLS w/o cert"
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
            "proto": "rsn",
            "pairwise": "ccmp",
            "proactive-key-caching": 1
        },
        "802-1x": {
            "auth-timeout": 0,
            "eap": "ttls",
            "identity": "'"${WL_USERNAME}"'",
            "password": "'"${WL_PASSWORD}"'",
            "anonymous-identity": "'"${ANONYMOUS_IDENTITY}"'",
            "phase2-autheap": "mschapv2",
            "phase2-autheap": "md5",
            "phase2-autheap": "gtc",
            "ca-cert": "'"${CA_CERT}"'",
            "client-cert": "None"
        }
    }'\
        | ${JQ_APP}

echo -e "\n"


