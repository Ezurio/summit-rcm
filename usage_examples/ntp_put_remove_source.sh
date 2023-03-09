source global_settings

echo -e "\n========================="
echo "Remove NTP sources"

${CURL_APP} -s --location \
    --request PUT ${URL}/ntp/removeSource \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data '{
        "sources": [
            "time.nist.gov"
        ]
    }'\
| ${JQ_APP}
echo -e "\n"

