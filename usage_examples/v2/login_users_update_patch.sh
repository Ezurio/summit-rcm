#! /bin/bash

source ../global_settings

TARGET_USER_USERNAME="${TARGET_USER_USERNAME:-"user1"}"
CURRENT_PASSWORD="${CURRENT_PASSWORD:-"currentpassword"}"
NEW_PASSWORD="${NEW_PASSWORD:-"newpassword"}"
PERMISSIONS="${PERMISSIONS:-""}"

echo "========================="
echo "Update a current user"
echo "========================="
echo

echo "Username: ${TARGET_USER_USERNAME}"
echo "Current Password: ${CURRENT_PASSWORD}"
echo "New Password: ${NEW_PASSWORD}"
echo "Permissions: ${PERMISSIONS}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PATCH ${URL}/api/v2/login/users/${TARGET_USER_USERNAME} \
    --header 'Content-Type: application/json' \
    -b cookie -c cookie --insecure \
    --data '{
        "currentPassword": "'"${CURRENT_PASSWORD}"'",
        "newPassword": "'"${NEW_PASSWORD}"'",
        "permissions": "'"${PERMISSIONS}"'"
    }' \
    -o >(${JQ_APP})

wait
