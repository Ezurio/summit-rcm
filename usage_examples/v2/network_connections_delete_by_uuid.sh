#! /bin/bash

UUID="${UUID:-"9e08345f-3e9e-4a11-a556-0c476d291c11"}"

source ../global_settings

echo "========================="
echo "Delete connection using explicit UUID"
echo "========================="
echo

echo "UUID: ${UUID}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request DELETE ${URL}/api/v2/network/connections/uuid/${UUID} \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
