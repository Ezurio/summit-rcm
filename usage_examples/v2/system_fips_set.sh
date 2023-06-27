#! /bin/bash

DESIRED_STATE="${DESIRED_STATE:-"unset"}"

source ../global_settings

echo "========================="
echo "Set current FIPS status"
echo "========================="
echo

echo "Desired FIPS State: ${DESIRED_STATE}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/system/fips \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data '{
        "state": "'"${DESIRED_STATE}"'"
    }' \
    -o >(${JQ_APP})

wait
