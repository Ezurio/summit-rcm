##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2025 Ezurio LLC.
##

IFNAME="${IFNAME:-"wlan0"}"
source ../global_settings

echo "========================="
echo "network interface available AP channels"
${CURL_APP} -s --header "Content-Type: application/json" \
    --request GET \
    ${URL}/networkInterfaceAvailableApChannels?name=${IFNAME} \
    -b cookie -c cookie --insecure \
| ${JQ_APP}
echo -e "\n"
