#! /bin/bash

source ../global_settings

echo "========================="
echo "Session login"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request POST ${URL}/api/v2/login \
    --header 'Content-Type: application/json' \
    -b cookie -c cookie --insecure \
    --data '{
        "username": "'"${SUMMIT_RCM_USERNAME}"'",
        "password": "'"${SUMMIT_RCM_PASSWORD}"'"
    }' \
    -o >(${JQ_APP})

wait
