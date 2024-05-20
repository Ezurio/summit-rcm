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

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request POST ${URL}/api/v2/system/update/updateFile \
    --header "Content-Type: application/octet-stream" \
    ${AUTH_OPT} \
    --data-binary @${FILE_PATH} \
    -o >(${JQ_APP})

wait

echo
echo "========================="
echo "Cancel any in-progress update"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/system/update \
    --header "Content-Type: application/json" \
    ${AUTH_OPT} \
    --data '{
        "status": 2,
        "url": "",
        "image": ""
    }' \
    -o >(${JQ_APP})

wait

IMAGE="${IMAGE:-"full"}"

echo
echo "========================="
echo "Initiate update"
echo "========================="
echo

echo "Image: ${IMAGE}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/system/update \
    --header "Content-Type: application/json" \
    ${AUTH_OPT} \
    --data '{
        "status": 5,
        "image": "'"${IMAGE}"'"
    }' \
    -o >(${JQ_APP})

wait

while true; do
    echo
    echo "========================="
    echo "Check status"
    echo "========================="
    echo
    echo -n "Status Code: "

    curl -s --location \
        -w "%{http_code}\nResponse:\n" \
        --request GET ${URL}/api/v2/system/update \
        ${AUTH_OPT} \
        -o >(${JQ_APP}) | tee status

    wait

    if grep -q "\"status\": 0" status; then
        echo "Update completed successfully."
        break
    fi
    if grep -q "\"status\": 1" status; then
        echo "Update failed."
        break
    fi
    sleep 1
done

echo
echo "Done"
