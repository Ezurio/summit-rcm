IFNAME="${IFNAME:-"wlan0"}"
source global_settings


echo -e "\n========================="
echo "Get networkinterface"

${CURL_APP} -s --location \
    --request GET ${URL}/networkInterface?name=${IFNAME} \
    -b cookie -c cookie --insecure \
| ${JQ_APP}

echo -e "\n"

