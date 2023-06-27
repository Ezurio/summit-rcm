source ../global_settings

echo -e "\n========================="
echo "AWM Get"

${CURL_APP} -s --location --request GET ${URL}/awm \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data-raw ''\
    | ${JQ_APP}

echo -e "\n"
