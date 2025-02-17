#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

ARCHIVE_PATH="${ARCHIVE_PATH:-"./debug.encrypt"}"

source ../global_settings

echo "========================="
echo "Export debug info"
echo "========================="
echo

echo "Archive Path: ${ARCHIVE_PATH}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\n" \
    --request GET ${URL}/api/v2/system/debug/export \
    -b cookie -c cookie --insecure \
    --output ${ARCHIVE_PATH}

wait

echo
echo "${ARCHIVE_PATH} file downloaded. To decrypt:"
echo "openssl cms -decrypt -in ${ARCHIVE_PATH} -recip /path/to/server.crt -inkey /path/to/server.key -out debug.zip -inform DER"
