#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

source ../global_settings

echo "========================="
echo "Update NTP sources"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/system/datetime/ntp \
    --header 'Content-Type: application/json' \
    -b cookie -c cookie --insecure \
    --data '[
        {
            "address": "time.nist.gov",
            "type": "static"
        }
    ]' \
    -o >(${JQ_APP})

wait
