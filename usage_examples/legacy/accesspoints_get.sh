##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings


echo -e "\n========================="
echo "Get accesspoints"

${CURL_APP} -s --location \
    --request GET ${URL}/accesspoints \
    ${AUTH_OPT} \
| ${JQ_APP}

echo -e "\n"

