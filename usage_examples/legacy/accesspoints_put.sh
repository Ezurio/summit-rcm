##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings

echo -e "\n========================="
echo "PUT accesspoints"

${CURL_APP} -s --header "Content-Type: application/json" \
    --request PUT "${URL}/accesspoints" \
    -b cookie -c cookie \
    --insecure \
    --data-raw ‘’\
| ${JQ_APP}

echo -e "\n"

