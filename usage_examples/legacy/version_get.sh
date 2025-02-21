##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings

echo -e "\n========================="
echo "Versions"

${CURL_APP} -s --header "Content-Type: application/json" \
    --location \
    --request GET ${URL}/version \
    ${AUTH_OPT} \
| ${JQ_APP}

echo -e "\n"

