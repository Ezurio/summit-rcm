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
    -b cookie -c cookie --insecure \
| ${JQ_APP}

echo -e "\n"

