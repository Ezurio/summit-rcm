LOGTYPE="${LOGTYPE:-"All"}"
PRIORITY="${PRIORITY:-6}"
DAYS="${DAYS:--1}"

source ../global_settings

echo -e "\n========================="
echo "Get LogData"

${CURL_APP} -s --location \
    --request GET "${URL}/logData?type=${LOGTYPE}&priority=${PRIORITY}&days=${DAYS}" \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
| ${JQ_APP}

echo -e "\n"

