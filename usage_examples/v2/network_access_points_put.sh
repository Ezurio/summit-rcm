#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

source ../global_settings

echo "========================="
echo "Request scan for access points"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/network/accessPoints/scan \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
