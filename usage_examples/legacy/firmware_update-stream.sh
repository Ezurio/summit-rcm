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
    --request DELETE --insecure \
    ${URL}/firmware -b cookie -c cookie | ${JQ_APP}

${CURL_APP} -s -S --header "Content-Type: application/json" \
    --request POST   --data \
    '{"image":"main"}'  --insecure \
    ${URL}/firmware -b cookie -c cookie | ${JQ_APP}

${CURL_APP} --request PUT ${URL}/firmware --header "Content-type: application/octet-stream" -b cookie -c cookie --insecure --data-binary @${FIRMWARE}

SUCCESS=false
echo
echo
while true; do
    echo "Checking status:"
    ${CURL_APP} -s --request GET --insecure ${URL}/firmware -b cookie -c cookie | tee status | ${JQ_APP}
    echo
    if grep -q Updated status; then
        SUCCESS=true
        break
    fi
    if grep -q Failed status; then
        break
    fi
    sleep 1
done

echo
${SUCCESS} && . $SCRIPTPATH/reboot_put.sh


echo ""
echo "Done"
