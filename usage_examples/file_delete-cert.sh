#FILE=user2.pem

source global_settings

echo ""
echo "========================="
echo "Delete cert file for Network Manager"

${CURL_APP} -s --request DELETE "${URL}/file?file=${FILE}&type=${TYPE}" \
    -b cookie -c cookie --insecure \
 #   | ${JQ_APP}

echo -e "\n"


