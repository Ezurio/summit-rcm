#! /bin/bash

source ../global_settings

echo "========================="
echo "Get all forwarded ports"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request GET ${URL}/api/v2/network/firewall/forwardedPorts \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
