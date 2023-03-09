source global_settings

echo -e "\n========================="
echo "Wifi enable Get"

${CURL_APP} -s --location --request GET ${URL}/wifiEnable \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data-raw ''\
    | ${JQ_APP}

echo -e "\n"
