#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

source ../global_settings

echo "========================="
echo "Remove virtual network interface (wlan1)"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request DELETE ${URL}/api/v2/network/interfaces/wlan1 \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
