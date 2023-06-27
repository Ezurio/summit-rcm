source ../global_settings
ENABLE="${ENABLE:-1}"

echo -e "\n\n========================="
echo "wifi enable put"
${CURL_APP} -s --location --request PUT "${URL}/wifiEnable?enable=${ENABLE}" \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data-raw '' \
| ${JQ_APP}

echo -e "\n"
