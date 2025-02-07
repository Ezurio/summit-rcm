#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2025 Ezurio LLC.
##

NAME="${NAME:-"wlan0"}"

source ../global_settings

echo "========================="
echo "Get the current DHCP leases for the network interface"
echo "========================="
echo

echo "Interface Name: ${NAME}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request GET ${URL}/api/v2/network/interfaces/${NAME}/dhcpLeases \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
