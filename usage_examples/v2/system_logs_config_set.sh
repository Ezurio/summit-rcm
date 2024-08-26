#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

source ../global_settings

# Supplicant Debug Levels:
# - none
# - error
# - warning
# - info
# - debug
# - msgdump
# - excessive
SUPPLICANT_DEBUG_LEVEL="${SUPPLICANT_DEBUG_LEVEL:-"none"}"

# Wi-Fi Driver Debug Levels:
# - 0
# - 1
WIFI_DRIVER_DEBUG_LEVEL="${WIFI_DRIVER_DEBUG_LEVEL:-0}"

echo "========================="
echo "Set log configuration"
echo "========================="
echo

echo "Supplicant Debug Level: ${SUPPLICANT_DEBUG_LEVEL}"
echo "Wi-Fi Driver Debug Level: ${WIFI_DRIVER_DEBUG_LEVEL}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\n" \
    --request PUT ${URL}/api/v2/system/logs/config \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data '{
        "suppDebugLevel": "'"${SUPPLICANT_DEBUG_LEVEL}"'",
        "driverDebugLevel": '"${WIFI_DRIVER_DEBUG_LEVEL}"'
    }' \
    -o >(${JQ_APP})

wait
