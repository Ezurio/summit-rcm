source ../global_settings
ENABLE="${ENABLE:-1}"

echo -e "\n\n========================="
echo "Modem enable put"
${CURL_APP} -s --location --request PUT "${URL}/modemEnable?enable=${ENABLE}" \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data-raw '' \
| ${JQ_APP}

echo -e "\n"
