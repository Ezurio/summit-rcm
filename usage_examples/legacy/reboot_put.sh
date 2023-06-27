source ../global_settings

echo -e "\n\n========================="
echo "Reboot"
${CURL_APP} -s --location --request PUT ${URL}/reboot \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data-raw ''\
| ${JQ_APP}


echo -e "\n"
