source global_settings

echo "========================="
echo "Connections"
${CURL_APP} -s --header "Content-Type: application/json" \
    --request GET \
    ${URL}/connections \
    -b cookie -c cookie --insecure \
| ${JQ_APP}

echo -e "\n"
