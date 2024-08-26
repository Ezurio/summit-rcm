##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings

echo "========================="
echo "network status"
${CURL_APP} -s --header "Content-Type: application/json" \
    --request GET \
    ${URL}/networkStatus \
    -b cookie -c cookie --insecure \
| ${JQ_APP}
echo -e "\n"
