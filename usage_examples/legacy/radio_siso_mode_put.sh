source ../global_settings
SISO_MODE="${SISO_MODE:-"-1"}"

echo -e "\n========================="
echo "Set radio SISO mode"

${CURL_APP} -s --location \
    --request PUT "${URL}/radioSISOMode?SISO_mode=${SISO_MODE}" \
    -b cookie -c cookie --insecure \
    --data-raw '' \
| ${JQ_APP}
echo -e "\n"

