#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

source ../global_settings

echo "========================="
echo "Get log forwarding state"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\n" \
    --request GET ${URL}/api/v2/system/logs/forwarding \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
