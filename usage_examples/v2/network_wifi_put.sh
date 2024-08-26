#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

WIFI_RADIO_SOFTWARE_ENABLED="${WIFI_RADIO_SOFTWARE_ENABLED:-true}"

source ../global_settings

echo "========================="
echo "Set Wi-Fi settings"
echo "========================="
echo

echo "Desired Wi-Fi Radio Software Enabled: ${WIFI_RADIO_SOFTWARE_ENABLED}"
# The Wi-Fi radio cannot be hardware disabled via software
echo "Desired Wi-Fi Radio Hardware Enabled: true"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/network/wifi \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data '{
        "wifiRadioSoftwareEnabled": '"${WIFI_RADIO_SOFTWARE_ENABLED}"',
        "wifiRadioHardwareEnabled": true
    }' \
    -o >(${JQ_APP})

wait
