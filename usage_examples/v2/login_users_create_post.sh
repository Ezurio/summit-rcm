#! /bin/bash

source ../global_settings

NEW_USER_USERNAME="${NEW_USER_USERNAME:-"user1"}"
NEW_USER_PASSWORD="${NEW_USER_PASSWORD:-"user1"}"
NEW_USER_PERMISSIONS="${NEW_USER_PERMISSIONS:-"status_networking"}"

echo "========================="
echo "Create new user"
echo "========================="
echo

echo "Username: ${NEW_USER_USERNAME}"
echo "Password: ${NEW_USER_PASSWORD}"
echo "Permissions: ${NEW_USER_PERMISSIONS}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request POST "${URL}"/api/v2/login/users \
    --header 'Content-Type: application/json' \
    -b cookie -c cookie --insecure \
    --data '{
        "username": "'"${NEW_USER_USERNAME}"'",
        "password": "'"${NEW_USER_PASSWORD}"'",
        "permissions": "'"${NEW_USER_PERMISSIONS}"'"
    }' \
    -o >(${JQ_APP})

wait
