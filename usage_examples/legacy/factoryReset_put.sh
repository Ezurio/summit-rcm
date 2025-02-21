##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings

echo -e "\n========================="
echo "Factory Reset"

${CURL_APP} -s --location --request PUT ${URL}/factoryReset \
    --header "Content-Type: application/json" \
    ${AUTH_OPT} \
    --data-raw ''\
| ${JQ_APP}

echo -e "\n\n========================="
echo "Reboot required"
echo -e "\n"
