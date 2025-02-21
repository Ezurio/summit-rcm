##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings


echo -e "\n========================="
echo "Get all certificates"

REQUEST_URL="${URL}/certificates"

${CURL_APP} -s --location \
    --request GET "${REQUEST_URL}" \
    ${AUTH_OPT} \
| ${JQ_APP}

echo -e "\n"

