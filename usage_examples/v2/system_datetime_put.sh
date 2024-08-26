#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

DATETIME_NOW=$(($(date +%s%N) / 1000))
DATETIME="${DATETIME:-$DATETIME_NOW}"
TZ="${TZ:-"Etc/UTC"}"

source ../global_settings

echo "========================="
echo "Set Date/Time/Timezone"
echo "========================="
echo

echo "Datetime: ${DATETIME}"
echo "Timezone: ${TZ}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/system/datetime \
    --header 'Content-Type: application/json' \
    -b cookie -c cookie --insecure \
    --data '{
        "datetime": "'"${DATETIME}"'",
        "zone": "'"${TZ}"'"
    }' \
    -o >(${JQ_APP})

wait
