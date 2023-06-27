#! /bin/bash

CERT_NAME="${CERT_NAME:-"test.crt"}"
REQUEST_URL="${URL}/api/v2/network/certificates?name=${CERT_NAME}"

source ../global_settings

echo "========================="
echo "Get certificate info"
echo "========================="
echo

echo "Certificate Name: ${CERT_NAME}"
echo -n "Status Code: "

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
        --data '{"password": "'"${PASSWORD}"'"}' \
        -o >(${JQ_APP})
fi

wait
