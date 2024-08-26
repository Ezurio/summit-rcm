#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

SISO_MODE="${SISO_MODE:--1}"

source ../global_settings

echo "========================="
echo "Set radio's SISO Mode"
echo "========================="
echo

echo "Desired SISO Mode: ${SISO_MODE}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/network/wifi/radioSISOMode \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data '{
        "sisoMode": '"${SISO_MODE}"'
    }' \
    -o >(${JQ_APP})

wait
