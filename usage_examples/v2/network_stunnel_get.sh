#! /bin/bash

source ../global_settings

echo "========================="
echo "Get stunnel state"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\n" \
    --request GET ${URL}/api/v2/network/stunnel \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
