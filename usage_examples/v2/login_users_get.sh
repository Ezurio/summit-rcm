#! /bin/bash

source ../global_settings

echo "========================="
echo "Get current user info by name"
echo "========================="
echo

echo "Username: ${SUMMIT_RCM_USERNAME}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request GET "${URL}"/api/v2/login/users/"${SUMMIT_RCM_USERNAME}" \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
