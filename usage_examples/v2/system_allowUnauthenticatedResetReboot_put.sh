#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

source ../global_settings

echo "========================="
echo "Put allowUnauthenticatedResetReboot"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\n" \
    --request PUT ${URL}/api/v2/system/allowUnauthenticatedResetReboot \
    -b cookie -c cookie --insecure \
    --header "Content-Type: application/json" \
    -o >(${JQ_APP})

wait
