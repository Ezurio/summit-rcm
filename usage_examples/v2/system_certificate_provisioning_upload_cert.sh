#! /bin/bash

CRT_FILE="${CRT_FILE:-"dev.crt"}"

source ../global_settings

echo "========================="
echo "Upload signed device server certificate"
echo "========================="

echo "Device server certificate file: ${CRT_FILE}"
echo -n "Status Code: "


curl -s --location \
    -w "%{http_code}\n" \
    --request PUT ${URL}/api/v2/system/certificateProvisioning \
    -b cookie -c cookie --insecure \
    --form 'certificate=@"'"${CRT_FILE}"'"' \
    -o >(${JQ_APP})

wait
