UUID="${UUID:-"a760e87e-e23a-4ea6-81f9-c4e29052db27"}"
EXTENDED="${EXTENDED:-false}"
source ../global_settings


echo -e "\n========================="
echo "Get connection"

REQUEST_URL="${URL}/connection?uuid=${UUID}"
if [ "${EXTENDED}" == true ]; then
    REQUEST_URL="${REQUEST_URL}&extended=true"
fi

${CURL_APP} -s --location \
    --request GET "${REQUEST_URL}" \
    -b cookie -c cookie --insecure \
| ${JQ_APP}

echo -e "\n"

