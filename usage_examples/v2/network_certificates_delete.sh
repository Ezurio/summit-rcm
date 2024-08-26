#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

CERT_NAME="${CERT_NAME:-"test.crt"}"

source ../global_settings

echo "========================="
echo "Remove certificate"
echo "========================="
echo

echo "Certificate Name: ${CERT_NAME}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request DELETE ${URL}/api/v2/network/certificates/${CERT_NAME} \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
