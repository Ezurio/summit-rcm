#! /bin/bash

source ../global_settings

echo "========================="
echo "Suspend"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/system/power \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data '{
        "state": "suspend"
    }' \
    -o >(${JQ_APP})

wait
