#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2025 Ezurio LLC.
##

source ../global_settings

FILE_PATH="${FILE_PATH:-"som60.swu"}"

echo "========================="
echo "Software update (file post)"
echo "========================="
echo
echo -n "Status Code: "

${CURL_APP} --request PUT ${URL}/firmware --header "Content-type: application/octet-stream" ${AUTH_OPT} --data-binary @${FILE_PATH}

wait

echo "========================="
echo "Cancel any in-progress update"
echo "========================="
echo

${CURL_APP} -s -S \
    --request DELETE \
    ${AUTH_OPT} \
    ${URL}/firmware | ${JQ_APP}

wait

echo
echo "========================="
echo "Initiate update"
echo "========================="
echo

${CURL_APP} -s -S --header "Content-Type: application/json" \
    --request POST   --data \
    '{"image":"full"}' ${AUTH_OPT} \
    ${URL}/firmware | ${JQ_APP}

wait

echo
echo
while true; do
    echo "Checking status:"
    ${CURL_APP} -s --request GET ${AUTH_OPT} ${URL}/firmware | tee status | ${JQ_APP}
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
