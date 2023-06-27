#! /bin/bash

source ../global_settings

echo "========================="
echo "Get system power status"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request GET ${URL}/api/v2/system/power \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
