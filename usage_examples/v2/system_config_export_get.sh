#! /bin/bash

ARCHIVE_PATH="${ARCHIVE_PATH:-"./config.zip"}"
ARCHIVE_PASSWORD="${ARCHIVE_PASSWORD:-"test"}"

source ../global_settings

echo "========================="
echo "Export system configuration"
echo "========================="
echo

echo "Archive Path: ${ARCHIVE_PATH}"
echo "Archive Password: ${ARCHIVE_PASSWORD}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\n" \
    --request GET ${URL}/api/v2/system/config/export \
    -b cookie -c cookie --insecure \
    --header "Content-Type: application/json" \
    --data '{
        "password": "'"${ARCHIVE_PASSWORD}"'"
    }' \
    --output ${ARCHIVE_PATH}

wait
