#! /bin/bash

source ../global_settings

echo "========================="
echo "Clear forwarded ports"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/network/firewall/forwardedPorts \
    -b cookie -c cookie --insecure \
    --header "Content-Type: application/json" \
    --data '[]' \
    -o >(${JQ_APP})

wait
