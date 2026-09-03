#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2026 Ezurio LLC.
##

CONNECTION_NAME="${CONNECTION_NAME:-"WPA3_SUITE_B_192"}"
SSID="${SSID:-"lab-wpa3-suiteb192"}"

source ../global_settings

echo "========================="
echo "Create WPA3 suite-b-192 EAP-TLS connection using server-issued UUID"
echo "========================="
echo

echo "Connection Name (id): ${CONNECTION_NAME}"
echo "SSID: ${SSID}"
echo "Identity: ${WL_USERNAME}"
echo "CA certificate: ${CA_CERT}"
echo "Client key bundle: ${PRIVATE_KEY}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request POST ${URL}/api/v2/network/connections \
    --header "Content-Type: application/json" \
    ${AUTH_OPT} \
    --data '{
        "connection": {
            "autoconnect": 1,
            "id": "'"${CONNECTION_NAME}"'",
            "interface-name": "wlan0",
            "type": "802-11-wireless"
        },
        "802-11-wireless": {
            "ssid": "'"${SSID}"'"
        },
        "802-11-wireless-security": {
            "key-mgmt": "wpa-eap-suite-b-192",
            "proto": ["wpa3"]
        },
        "802-1x": {
            "eap": ["tls"],
            "identity": "'"${WL_USERNAME}"'",
            "client-cert": "'"${PRIVATE_KEY}"'",
            "private-key": "'"${PRIVATE_KEY}"'",
            "private-key-password": "'"${PRIVATE_KEY_PASSWORD}"'",
            "ca-cert": "'"${CA_CERT}"'"
        }
    }' \
    -o >(${JQ_APP})

wait
