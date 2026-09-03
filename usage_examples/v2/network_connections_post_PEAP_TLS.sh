#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2026 Ezurio LLC.
##

CONNECTION_NAME="${CONNECTION_NAME:-"PEAP_TLS"}"
SSID="${SSID:-"lab-peap-tls"}"

source ../global_settings

echo "========================="
echo "Create PEAP TLS connection using server-issued UUID"
echo "========================="
echo

echo "Connection Name (id): ${CONNECTION_NAME}"
echo "SSID: ${SSID}"
echo "Identity: ${WL_USERNAME}"
echo "CA certificate: ${CA_CERT}"
echo "Phase 2 client key bundle: ${PRIVATE_KEY}"
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
            "eap": ["peap"],
            "identity": "'"${WL_USERNAME}"'",
            "phase2-auth": "tls",
            "phase1-peapver": "0",
            "phase2-client-cert": "'"${PRIVATE_KEY}"'",
            "phase2-private-key": "'"${PRIVATE_KEY}"'",
            "phase2-private-key-password": "'"${PRIVATE_KEY_PASSWORD}"'",
            "phase2-ca-cert": "'"${CA_CERT}"'",
            "ca-cert": "'"${CA_CERT}"'"
        }
    }' \
    -o >(${JQ_APP})

wait
