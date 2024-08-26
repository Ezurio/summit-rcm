#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

CERT_NAME="${CERT_NAME:-"test.crt"}"

source ../global_settings

echo "========================="
echo "Get certificate info"
echo "========================="
echo

echo "Certificate Name: ${CERT_NAME}"
echo -n "Status Code: "

REQUEST_URL="${URL}/api/v2/network/certificates/${CERT_NAME}"

if [ -z "${PASSWORD+set}" ]; then
    curl -s --location \
        -w "%{http_code}\nResponse:\n" \
        --request GET "${REQUEST_URL}" \
        -b cookie -c cookie --insecure \
        -o >(${JQ_APP})
else
    curl -s --location \
        -w "%{http_code}\nResponse:\n" \
        --request GET "${REQUEST_URL}" \
        -b cookie -c cookie --insecure \
        --header "Content-Type: application/json" \
        --data '{"password": "'"${PASSWORD}"'"}' \
        -o >(${JQ_APP})
fi

wait
