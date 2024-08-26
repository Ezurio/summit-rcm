#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

FILE_NAME="${FILE_NAME:-"test.crt"}"
FILE_PATH="${FILE_PATH:-"./test.crt"}"

source ../global_settings

echo "========================="
echo "Upload certificate or PAC file for use by NetworkManager"
echo "========================="
echo

echo "File Name: ${FILE_NAME}"
echo "File Path: ${FILE_PATH}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request POST ${URL}/api/v2/network/certificates/${FILE_NAME} \
    -b cookie -c cookie --insecure \
    --form 'file=@"'"${FILE_PATH}"'"' \
    -o >(${JQ_APP})

wait
