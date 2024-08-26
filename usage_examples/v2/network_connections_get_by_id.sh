#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

CONNECTION_NAME="${CONNECTION_NAME:-"connection-id"}"

source ../global_settings

echo "========================="
echo "Get connection using connection name (id)"
echo "========================="
echo

echo "Connection Name (id): ${CONNECTION_NAME}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request GET ${URL}/api/v2/network/connections/id/${CONNECTION_NAME} \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
