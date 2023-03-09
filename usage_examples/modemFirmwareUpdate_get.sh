source global_settings

echo -e "\n========================="
echo "Modem Firmware Update Get"

${CURL_APP} -s --location --request GET ${URL}/modemFirmwareUpdate \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data-raw ''\
    | ${JQ_APP}

echo -e "\n"
