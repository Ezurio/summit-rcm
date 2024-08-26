##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
IFNAME="${IFNAME:-"wlan0"}"
source ../global_settings

echo "========================="
echo "network interface driver info"
${CURL_APP} -s --header "Content-Type: application/json" \
    --request GET \
    ${URL}/networkInterfaceDriverInfo?name=${IFNAME} \
    -b cookie -c cookie --insecure \
| ${JQ_APP}
echo -e "\n"
