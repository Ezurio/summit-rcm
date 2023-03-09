source global_settings
IP_VERSION="${IP_VERSION:-"ipv4"}"

echo -e "\n========================="
echo "Port forward"

if [ -z "$PORT" ]
then
    echo "Please invoke with port set e.g. PORT=22 $0"
    exit
fi
if [ -z "$PROTOCOL" ]
then
    echo "Please invoke with protocol set e.g. PROTOCOL=tcp/udp $0"
    exit
fi
if [ -z "$TOPORT" ]
then
    echo "Please invoke with to port set e.g. TOPORT=22 $0"
    exit
fi
if [ -z "$TOADDR" ]
then
    echo "Please invoke with to addr set e.g. TOADDR=10.10.5.6 $0"
    exit
fi


echo -e "\nforward port ${PORT}:\n"

${CURL_APP} --location --request PUT ${URL}/firewall/addForwardPort \
    --header "Content-Type: application/json" \
    -b cookie --insecure\
    --data '{
        "port": "'"${PORT}"'",
        "protocol": "'"${PROTOCOL}"'",
        "toport": "'"${TOPORT}"'",
        "toaddr": "'"${TOADDR}"'",
        "ip_version": "'"${IP_VERSION}"'"
        }' \
    | ${JQ_APP}

echo -e "\n\ncheck forwarded ports:\n"
${CURL_APP} --location --request GET ${URL}/firewall \
    --header "Content-Type: application/json" \
    -b cookie --insecure\
    | ${JQ_APP}


