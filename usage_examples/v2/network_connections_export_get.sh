#! /bin/bash

ARCHIVE_PATH="${ARCHIVE_PATH:-"./connections.zip"}"
ARCHIVE_PASSWORD="${ARCHIVE_PASSWORD:-"1234"}"

source ../global_settings

echo "========================="
echo "Export network connections"
echo "========================="
echo

echo "Archive Path: ${ARCHIVE_PATH}"
echo "Archive Password: ${ARCHIVE_PASSWORD}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\n" \
    --request GET ${URL}/api/v2/network/connections/export \
    -b cookie -c cookie --insecure \
    --header "Content-Type: application/json" \
    --data '{
        "password": "'"${ARCHIVE_PASSWORD}"'"
    }' \
    --output ${ARCHIVE_PATH}

wait
