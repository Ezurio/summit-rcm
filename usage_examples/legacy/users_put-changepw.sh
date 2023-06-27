source ../global_settings

echo ""
echo "====="
echo "Change password"

${CURL_APP} -s --header "Content-Type: application/json" \
    --request PUT \
    --data '{"username":"'"${SUMMIT_RCM_USERNAME}"'","current_password":"'"${ORIGINAL_SUMMIT_RCM_PASSWORD}"'","new_password":"'"${SUMMIT_RCM_PASSWORD}"'"}' \
    --insecure ${URL}/users \
    -b cookie -c cookie \
| ${JQ_APP}

echo -e "\n"
