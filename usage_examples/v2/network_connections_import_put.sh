#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

ARCHIVE_PATH="${ARCHIVE_PATH:-"./connections.zip"}"
ARCHIVE_PASSWORD="${ARCHIVE_PASSWORD:-"1234"}"
OVERWRITE_EXISTING="${OVERWRITE_EXISTING:-false}"

source ../global_settings

echo "========================="
echo "Import network connections"
echo "========================="
echo

echo "Archive Path: ${ARCHIVE_PATH}"
echo "Archive Password: ${ARCHIVE_PASSWORD}"
echo "Overwrite Existing: ${OVERWRITE_EXISTING}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/network/connections/import \
    -b cookie -c cookie --insecure \
    --form 'archive=@"'${ARCHIVE_PATH}'"' \
    --form 'config="{
            \"overwrite\": '"${OVERWRITE_EXISTING}"',
            \"password\": \"'"${ARCHIVE_PASSWORD}"'\"
        }";type=application/json' \
    -o >(${JQ_APP})

wait
