source ../global_settings

echo -e "\n========================="
echo "Bluetooth Get State Info"

${CURL_APP} --location -s --request GET ${URL}/bluetooth \
    -b cookie -c cookie --insecure\
    | ${JQ_APP}
echo -e '\n'
