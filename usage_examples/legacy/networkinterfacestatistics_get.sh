IFNAME="${IFNAME:-"wlan0"}"
source ../global_settings

echo "========================="
echo "network interface statistics"
${CURL_APP} -s --header "Content-Type: application/json" \
    --request GET \
    ${URL}/networkInterfaceStatistics?name=${IFNAME} \
    -b cookie -c cookie --insecure \
| ${JQ_APP}
echo -e "\n"
