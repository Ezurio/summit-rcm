source global_settings

echo -e "\n========================="
echo "Get NTP sources"

${CURL_APP} -s --location \
    --request GET "${URL}/ntp" \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
| ${JQ_APP}
echo -e "\n"

