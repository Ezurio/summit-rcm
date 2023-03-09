source global_settings

echo -e "\n========================="
echo "Activate stunnel"

${CURL_APP} -s --location \
    --request PUT ${URL}/stunnel \
    --header "Content-Type: application/json" \
    -b cookie --insecure \
    --data-raw '{"state":"active"}' \
| ${JQ_APP}

echo -e "\n"

