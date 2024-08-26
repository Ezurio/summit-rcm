#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

ARCHIVE_PATH="${ARCHIVE_PATH:-"./config.zip"}"
ARCHIVE_PASSWORD="${ARCHIVE_PASSWORD:-"test"}"

source ../global_settings

echo "========================="
echo "Import system configuration"
echo "========================="
echo

echo "Archive Path: ${ARCHIVE_PATH}"
echo "Archive Password: ${ARCHIVE_PASSWORD}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/system/config/import \
    -b cookie -c cookie --insecure \
    --form 'archive=@"'${ARCHIVE_PATH}'"' \
    --form 'password="'${ARCHIVE_PASSWORD}'"' \
    -o >(${JQ_APP})

wait
