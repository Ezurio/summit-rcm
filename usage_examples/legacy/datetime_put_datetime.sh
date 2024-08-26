##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
DATETIME_NOW=$(($(date +%s%N)/1000))
DATETIME="${DATETIME:-$DATETIME_NOW}"

source ../global_settings

echo -e "\n========================="
echo "Set datetime"

${CURL_APP} -s --location \
    --request PUT "${URL}/datetime" \
    --header 'Content-Type: application/json' \
    --data '{
    "datetime": "'"${DATETIME}"'","method": "manual"
    }' \
    --insecure \
    -b cookie -c cookie \
    | ${JQ_APP}



