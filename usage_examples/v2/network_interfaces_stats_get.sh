#! /bin/bash

NAME="${NAME:-"wlan0"}"

source ../global_settings

echo "========================="
echo "Get network interface stats by name"
echo "========================="
echo

echo "Interface Name: ${NAME}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request GET ${URL}/api/v2/network/interfaces/${NAME}/stats \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
