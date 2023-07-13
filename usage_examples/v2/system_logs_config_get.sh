#! /bin/bash

source ../global_settings

echo "========================="
echo "Get log configuration"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\n" \
    --request GET ${URL}/api/v2/system/logs/config \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
