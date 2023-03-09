source global_settings

echo -e "\n========================="
echo "Get stunnel state"

${CURL_APP} -s --location \
    --request GET ${URL}/stunnel \
    --header "Content-Type: application/json" \
    -b cookie --insecure \
    --data-raw '' \
| ${JQ_APP}

echo -e "\n"

