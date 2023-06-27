#! /bin/bash

source ../global_settings

echo "========================="
echo "Get current FIPS status"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request GET ${URL}/api/v2/system/fips \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
