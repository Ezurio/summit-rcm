source ../global_settings

echo -e "\n========================="
echo "Get radio SISO mode"

${CURL_APP} -s --location \
    --request GET "${URL}/radioSISOMode" \
    -b cookie -c cookie --insecure \
| ${JQ_APP}
echo -e "\n"

