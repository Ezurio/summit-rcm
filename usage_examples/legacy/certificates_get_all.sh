source ../global_settings


echo -e "\n========================="
echo "Get all certificates"

REQUEST_URL="${URL}/certificates"

${CURL_APP} -s --location \
    --request GET "${REQUEST_URL}" \
    -b cookie -c cookie --insecure \
| ${JQ_APP}

echo -e "\n"

