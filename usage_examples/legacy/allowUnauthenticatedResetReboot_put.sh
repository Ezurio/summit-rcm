source ../global_settings

echo -e "\n\n========================="
echo "set allow unauthenticated reset and reboot"

${CURL_APP} -s --location --request PUT ${URL}/allowUnauthenticatedResetReboot \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data-raw ''\
| ${JQ_APP}


echo -e "\n"
