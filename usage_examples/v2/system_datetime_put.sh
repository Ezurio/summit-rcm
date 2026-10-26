#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

DATETIME_NOW=$(($(date +%s%N) / 1000))
DATETIME="${DATETIME:-$DATETIME_NOW}"

source ../global_settings

echo "========================="
echo "Set Date/Time"
echo "========================="
echo

echo "Datetime: ${DATETIME}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/system/datetime \
    --header 'Content-Type: application/json' \
    ${AUTH_OPT} \
    --data '{
        "datetime": "'"${DATETIME}"'"
    }' \
    -o >(${JQ_APP})

wait
