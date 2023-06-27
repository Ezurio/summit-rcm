source ../global_settings

echo -e "\n========================="
echo "Fips GET"

${CURL_APP} -s --location --request GET ${URL}/fips \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data-raw ''\
    | ${JQ_APP}

echo -e "\n========================="
echo "Fips PUT"

echo -e "empty:\n"
${CURL_APP} -s --location --request PUT ${URL}/fips \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data '{}'\
    | ${JQ_APP}
echo -e '\n'

echo -e "invalid:\n"
${CURL_APP} -s --location --request PUT ${URL}/fips \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data '{"fips":"status"}'\
    | ${JQ_APP}
echo -e '\n'

echo -e "fips:\n"
${CURL_APP} -s --location --request PUT ${URL}/fips \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data '{"fips":"fips"}'\
    | ${JQ_APP}

echo -e "unset:\n"
${CURL_APP} -s --location --request PUT ${URL}/fips \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data '{"fips":"unset"}'\
    | ${JQ_APP}

echo -e "\nChange in FIPS state not active until system reboot"
