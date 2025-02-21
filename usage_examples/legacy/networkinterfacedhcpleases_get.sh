##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2025 Ezurio LLC.
##

IFNAME="${IFNAME:-"wlan0"}"
source ../global_settings

echo "========================="
echo "network interface current DHCP leases"
${CURL_APP} -s --header "Content-Type: application/json" \
    --request GET \
    ${URL}/networkInterfaceDhcpLeases?name=${IFNAME} \
    ${AUTH_OPT} \
| ${JQ_APP}
echo -e "\n"
