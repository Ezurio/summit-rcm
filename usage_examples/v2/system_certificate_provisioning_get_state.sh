#! /bin/bash

source ../global_settings

echo "========================="
echo "Get current provisioning state"
echo "========================="

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\n" \
    --request GET ${URL}/api/v2/system/certificateProvisioning \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
