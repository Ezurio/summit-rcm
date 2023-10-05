#! /bin/bash

source ../global_settings

echo "========================="
echo "Delete allowUnauthenticatedResetReboot"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\n" \
    --request DELETE ${URL}/api/v2/system/allowUnauthenticatedResetReboot \
    -b cookie -c cookie --insecure \
    --header "Content-Type: application/json" \
    -o >(${JQ_APP})

wait
