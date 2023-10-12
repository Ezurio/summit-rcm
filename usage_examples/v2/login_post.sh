#! /bin/bash

source ../global_settings

echo "========================="
echo "Session login"
echo "========================="
echo

echo "Attempting to login with $SUMMIT_RCM_PASSWORD"

http_code=$(curl -s --location \
    -w "%{http_code}" \
    --request POST "${URL}"/api/v2/login \
    --header 'Content-Type: application/json' \
    -b cookie -c cookie --insecure \
    --data '{
        "username": "'"${SUMMIT_RCM_USERNAME}"'",
        "password": "'"${SUMMIT_RCM_PASSWORD}"'"
    }')

echo "Status Code: $http_code"

if [ "$http_code" = "403" ]; then
    echo "Unable to login with $SUMMIT_RCM_PASSWORD"
    echo "Attempting to login with $ORIGINAL_SUMMIT_RCM_PASSWORD"
    http_code=$(curl -s --location \
        -w "%{http_code}" \
        --request POST "${URL}"/api/v2/login \
        --header 'Content-Type: application/json' \
        -b cookie -c cookie --insecure \
        --data '{
            "username": "'"${SUMMIT_RCM_USERNAME}"'",
            "password": "'"${ORIGINAL_SUMMIT_RCM_PASSWORD}"'"
        }')
    if [ "$http_code" = "200" ]; then
        echo "Status Code: $http_code"
        echo "Login Successful"
        echo "Please considering changing the default password!"
        echo "See usage_examples/v2/login_users_update_password.sh"
    fi
elif [ "$http_code" = "200" ]; then
    echo "Login Successful"
fi

wait
