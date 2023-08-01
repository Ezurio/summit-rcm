#! /bin/bash

source ../global_settings

DESIRED_STATE="${DESIRED_STATE:-"active"}"

echo "========================="
echo "Set stunnel state"
echo "========================="
echo

echo "Desired stunnel State: ${DESIRED_STATE}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\n" \
    --request PUT ${URL}/api/v2/network/stunnel \
    -b cookie -c cookie --insecure \
    --header "Content-Type: application/json" \
    --data '{
        "state": "'"${DESIRED_STATE}"'"
    }' \
    -o >(${JQ_APP})

wait
