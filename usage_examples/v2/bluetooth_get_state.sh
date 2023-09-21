#! /bin/bash

source ../global_settings

echo "========================="
echo "Get Bluetooth state info"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request GET ${URL}/api/v2/bluetooth \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
