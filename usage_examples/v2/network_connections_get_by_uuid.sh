#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

UUID="${UUID:-"a760e87e-e23a-4ea6-81f9-c4e29052db27"}"

source ../global_settings

echo "========================="
echo "Get connection using explicit UUID"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request GET ${URL}/api/v2/network/connections/uuid/${UUID} \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
