source ../global_settings

echo ""
echo "====="
echo "Login"

${CURL_APP} -s --header "Content-Type: application/json" \
    --request POST \
    --data '{"username":"'"${SUMMIT_RCM_USERNAME}"'","password":"'"${SUMMIT_RCM_PASSWORD}"'"}' \
    --insecure ${URL}/login \
    -c cookie -b cookie \
| ${JQ_APP}


echo -e "\n"
