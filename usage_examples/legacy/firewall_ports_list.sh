##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings

echo -e "\n========================="
echo "List forwarded ports"

echo -e "\n\ncheck forwarded ports:\n"
${CURL_APP} --location --request GET ${URL}/firewall \
    --header "Content-Type: application/json" \
    ${AUTH_OPT} \
    | ${JQ_APP}


