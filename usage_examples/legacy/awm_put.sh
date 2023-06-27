source ../global_settings

echo -e "\n========================="
echo "AWM PUT"

echo -e "empty:\n"
${CURL_APP} -s --location --request PUT ${URL}/awm \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data '{}' \
    | ${JQ_APP}
echo -e '\n'

 echo -e "\nset:\n"
 ${CURL_APP} -s --location --request PUT ${URL}/awm \
     --header "Content-Type: application/json" \
     -b cookie -c cookie --insecure\
     --data '{"geolocation_scanning_enable":1}' \
     | ${JQ_APP}
 echo -e '\n'

 echo -e "\nunset:\n"
 ${CURL_APP} -s --location --request PUT ${URL}/awm \
     --header "Content-Type: application/json" \
     -b cookie -c cookie --insecure\
     --data '{"geolocation_scanning_enable":0}' \
     | ${JQ_APP}

echo -e "\n"
