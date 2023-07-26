#! /bin/bash

source ../global_settings

echo "========================="
echo "Get NTP sources"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request GET ${URL}/api/v2/system/datetime/ntp \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
