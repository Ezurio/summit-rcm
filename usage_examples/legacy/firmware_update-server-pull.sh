##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
FIRMWARE="${1}"

if [ -z "${FIRMWARE}" ]; then
    echo usage: ${0} firmware url, e.g. http://192.168.1.123:8080/som60.swu
    exit
fi
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

. ${SCRIPTPATH}/../global_settings

echo "========================="
echo "Cancel any in-progress update"
echo "========================="
echo

${CURL_APP} -s -S \
    --request DELETE \
    ${AUTH_OPT} \
    ${URL}/firmware | ${JQ_APP}

wait

echo -e "\n\n========================="
echo "Firmware update"
echo "========================="
echo "Requesting device pull FW from ${FIRMWARE}..."
echo
${CURL_APP} -s --header "Content-Type: application/json" \
    --request POST   --data \
    '{"image":"full", "url":"'"${FIRMWARE}"'"}' \
    ${AUTH_OPT} \
    ${URL}/firmware

echo
echo
while true; do
    echo "Checking status:"
    ${CURL_APP} -s --request GET ${URL}/firmware ${AUTH_OPT} | tee status | ${JQ_APP}
    echo
    if grep -q Updated status; then
        echo "Update completed successfully"
        break
    fi
    if grep -q Failed status; then
        echo "Update failed"
        break
    fi
    sleep 1
done


echo ""
echo "Done"
