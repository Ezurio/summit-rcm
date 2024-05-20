##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
FIRMWARE="${1}"

if [ -z "${FIRMWARE}" ]; then
    echo usage: ${0} update file
    exit
fi

if [ ! -e "${FIRMWARE}" ]; then
    echo \"${FIRMWARE}\": file not found
    exit
fi
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

. ${SCRIPTPATH}/../global_settings


echo -e "\n\n========================="
echo "Firmware update (streaming)"
echo "========================="
${CURL_APP} -s -S \
    --request DELETE \
    ${AUTH_OPT} \
    ${URL}/firmware | ${JQ_APP}

echo
echo "========================="
echo "Start update process"
echo "========================="

${CURL_APP} -s -S --header "Content-Type: application/json" \
    --request POST   --data \
    '{"image":"full"}' \
    ${AUTH_OPT} \
    ${URL}/firmware | ${JQ_APP}

echo
echo "========================="
echo "Send update file"
echo "========================="

${CURL_APP} --request PUT ${URL}/firmware --header "Content-type: application/octet-stream" ${AUTH_OPT} --data-binary @${FIRMWARE}

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
