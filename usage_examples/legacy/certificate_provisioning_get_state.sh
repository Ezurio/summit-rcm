source ../global_settings

echo -e "\n========================="
echo "Get current provisioning state"
echo

REQUEST_URL="${URL}/certificateProvisioning"

${CURL_APP} -s --location \
    --request GET "${REQUEST_URL}" \
    -b cookie -c cookie --insecure \
| ${JQ_APP}

echo -e "\n"
