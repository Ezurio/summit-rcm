#! /bin/bash

source ../global_settings

PERMISSIONS="${PERMISSIONS:-""}"

echo "========================="
echo "Update a current user"
echo "========================="
echo

echo "Username: ${SUMMIT_RCM_USERNAME}"
echo "Current Password: ${ORIGINAL_SUMMIT_RCM_PASSWORD}"
echo "New Password: ${SUMMIT_RCM_PASSWORD}"
echo "Permissions: ${PERMISSIONS}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PATCH "${URL}"/api/v2/login/users/"${SUMMIT_RCM_USERNAME}" \
    --header 'Content-Type: application/json' \
    -b cookie -c cookie --insecure \
    --data '{
        "currentPassword": "'"${ORIGINAL_SUMMIT_RCM_PASSWORD}"'",
        "newPassword": "'"${SUMMIT_RCM_PASSWORD}"'",
        "permissions": "'"${PERMISSIONS}"'"
    }' \
    -o >(${JQ_APP})

wait
