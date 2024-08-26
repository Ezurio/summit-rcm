#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

source ../global_settings

echo "========================="
echo "Session logout"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request DELETE ${URL}/api/v2/login \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
