#! /bin/bash

source ../global_settings

TARGET_USER_USERNAME="${TARGET_USER_USERNAME:-"user1"}"

echo "========================="
echo "Get current user info by name"
echo "========================="
echo

echo "Username: ${TARGET_USER_USERNAME}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request GET ${URL}/api/v2/login/users/${TARGET_USER_USERNAME} \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
