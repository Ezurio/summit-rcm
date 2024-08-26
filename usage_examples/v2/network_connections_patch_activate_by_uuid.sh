#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

UUID="${UUID:-"9e08345f-3e9e-4a11-a556-0c476d291c11"}"
ACTIVATED="${ACTIVATED:-true}"

source ../global_settings

echo "========================="
echo "Activate/deactivate connection using explicit UUID"
echo "========================="
echo

echo "Desired Activation State: ${ACTIVATED}"
echo "UUID: ${UUID}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PATCH ${URL}/api/v2/network/connections/uuid/${UUID} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data '{
        "connection": {
            "activated": '"${ACTIVATED}"'
        }
    }' \
    -o >(${JQ_APP})

wait
