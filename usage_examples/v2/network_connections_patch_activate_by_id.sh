#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

CONNECTION_NAME="${CONNECTION_NAME:-"connection-id"}"
ACTIVATED="${ACTIVATED:-true}"

source ../global_settings

echo "========================="
echo "Activate/deactivate connection connection name (id)"
echo "========================="
echo

echo "Desired Activation State: ${ACTIVATED}"
echo "Connection Name (id): ${CONNECTION_NAME}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PATCH ${URL}/api/v2/network/connections/id/${CONNECTION_NAME} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data '{
        "connection": {
            "activated": '"${ACTIVATED}"'
        }
    }' \
    -o >(${JQ_APP})

wait
