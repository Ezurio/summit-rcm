##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
TZ="${TZ:-"America/Los_Angeles"}"

source ../global_settings

echo -e "\n========================="
echo "Set time zone"

${CURL_APP} -s --location \
    --request PUT "${URL}/datetime" \
    --header 'Content-Type: application/json' \
    --data '{
    "zone": "'"${TZ}"'"
    }' \
    ${AUTH_OPT} \
    | ${JQ_APP}



