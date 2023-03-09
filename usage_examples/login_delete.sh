source global_settings

# Logout
echo ""
echo "======"
echo "logout"
${CURL_APP} -s --header "Content-Type: application/json" \
    --request DELETE \
    --insecure ${URL}/login \
    -b cookie \
| ${JQ_APP}

echo -e "\n"


