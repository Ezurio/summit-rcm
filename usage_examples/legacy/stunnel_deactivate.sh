##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings

echo -e "\n========================="
echo "Deactivate stunnel"

${CURL_APP} -s --location \
    --request PUT ${URL}/stunnel \
    --header "Content-Type: application/json" \
    -b cookie --insecure \
    --data-raw '{"state":"inactive"}' \
| ${JQ_APP}

echo -e "\n"

