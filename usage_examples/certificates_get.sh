source global_settings
CERT_NAME="${CERT_NAME:-"test.crt"}"
PASSWORD="${PASSWORD:-""}"

echo -e "\n========================="
echo "Get certificate info"

REQUEST_URL="${URL}/certificates?name=${CERT_NAME}&password=${PASSWORD}"

${CURL_APP} -s --location \
    --request GET "${REQUEST_URL}" \
    -b cookie -c cookie --insecure \
| ${JQ_APP}

echo -e "\n"

