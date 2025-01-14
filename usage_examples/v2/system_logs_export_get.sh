#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

ARCHIVE_PATH="${ARCHIVE_PATH:-"./logs.zip"}"
ARCHIVE_PASSWORD="${ARCHIVE_PASSWORD:-"1234"}"

source ../global_settings

echo "========================="
echo "Export logs"
echo "========================="
echo

echo "Archive Path: ${ARCHIVE_PATH}"
echo "Archive Password: ${ARCHIVE_PASSWORD}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\n" \
    --request GET ${URL}/api/v2/system/logs/export \
    -b cookie -c cookie --insecure \
    --header "Content-Type: application/json" \
    --data '{
        "password": "'"${ARCHIVE_PASSWORD}"'"
    }' \
    --output ${ARCHIVE_PATH}

wait
