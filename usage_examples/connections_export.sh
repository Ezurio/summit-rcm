source global_settings
ARCHIVE_PASSWORD="${ARCHIVE_PASSWORD:-"1234"}"

echo "========================="
echo "Export connections"
${CURL_APP} -s --location \
    --header "Content-Type: application/json" \
    --request GET \
    "${URL}/files?type=network&password=${ARCHIVE_PASSWORD}" \
    -b cookie -c cookie --insecure \
    --data-raw '' \
    --output connections.zip

echo -e "\n"
