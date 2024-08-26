#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

SCANNING_ENABLED="${SCANNING_ENABLED:-1}"

source ../global_settings

echo "========================="
echo "Set AWM Mode"
echo "========================="
echo

echo "Desired Geolocation Scanning Enabled: ${SCANNING_ENABLED}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/network/wifi/awm \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data '{
        "geolocationScanningEnabled": '"${SCANNING_ENABLED}"'
    }' \
    -o >(${JQ_APP})

wait
