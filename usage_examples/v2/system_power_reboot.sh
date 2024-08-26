#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

source ../global_settings

echo "========================="
echo "Reboot"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/system/power \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data '{
        "state": "reboot"
    }' \
    -o >(${JQ_APP})

wait
