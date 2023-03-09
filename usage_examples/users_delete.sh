USR="${USR:-"test"}"

source global_settings

echo -e "\n========================="
echo "del user"

${CURL_APP} -s --location \
    --request DELETE ${URL}/users?username=${USR} \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    | ${JQ_APP}

echo -e "\n"

