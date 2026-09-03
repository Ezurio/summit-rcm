#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2026 Ezurio LLC.
##

CONNECTION_NAME="${CONNECTION_NAME:-"EAP_TTLS_GTC"}"
SSID="${SSID:-"lab-eap-ttls"}"

source ../global_settings

echo "========================="
echo "Create EAP-TTLS GTC connection using server-issued UUID"
echo "========================="
echo

echo "Connection Name (id): ${CONNECTION_NAME}"
echo "SSID: ${SSID}"
echo "Identity: ${WL_USERNAME}"
echo "Anonymous identity: ${ANONYMOUS_IDENTITY}"
echo "CA certificate: ${CA_CERT}"
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
            "key-mgmt": "wpa-eap",
            "proto": ["rsn"]
        },
        "802-1x": {
            "eap": ["ttls"],
            "identity": "'"${WL_USERNAME}"'",
            "password": "'"${WL_PASSWORD}"'",
            "anonymous-identity": "'"${ANONYMOUS_IDENTITY}"'",
            "phase2-autheap": "gtc",
            "ca-cert": "'"${CA_CERT}"'"
        }
    }' \
    -o >(${JQ_APP})

wait
