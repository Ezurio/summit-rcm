#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2026 Ezurio LLC.
##

TZ="${TZ:-"Etc/UTC"}"

source ../global_settings

echo "========================="
echo "Set Timezone"
echo "========================="
echo

echo "Timezone: ${TZ}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/system/datetime \
    --header 'Content-Type: application/json' \
    ${AUTH_OPT} \
    --data '{
        "zone": "'"${TZ}"'"
    }' \
    -o >(${JQ_APP})

wait
