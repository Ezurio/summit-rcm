#! /bin/bash

source ../global_settings

echo "========================="
echo "Add virtual network interface (wlan1)"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/network/interfaces/wlan1 \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
