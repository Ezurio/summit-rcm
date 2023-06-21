#! /bin/bash

ARCHIVE_PATH="${ARCHIVE_PATH:-"./connections.zip"}"
ARCHIVE_PASSWORD="${ARCHIVE_PASSWORD:-"1234"}"

source ../global_settings

echo "========================="
echo "Import network connections"
echo "========================="
echo

echo "Archive Path: ${ARCHIVE_PATH}"
echo "Archive Password: ${ARCHIVE_PASSWORD}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/network/connections/import \
    -b cookie -c cookie --insecure \
    --form 'archive=@"'${ARCHIVE_PATH}'"' \
    --form 'password="'${ARCHIVE_PASSWORD}'"' \
    -o >(${JQ_APP})

wait
