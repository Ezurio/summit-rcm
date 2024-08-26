#! /bin/bash
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

IMAGE="${IMAGE:-"full"}"

echo "========================="
echo "System update (server pull)"
echo "========================="
echo

echo "========================="
echo "Initiate update"
echo "========================="
echo

echo "Firmware URL: ${FIRMWARE}"
echo "Image: ${IMAGE}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/system/update \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data '{
        "status": 5,
        "url": "'"${FIRMWARE}"'",
        "image": "'"${IMAGE}"'"
    }' \
    -o >(${JQ_APP})

wait

SUCCESS=false

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
        -b cookie -c cookie --insecure \
        -o >(${JQ_APP}) | tee status | ${JQ_APP}

    wait

    if grep -q "\"status\": 0" status; then
        SUCCESS=true
        break
    fi
    if grep -q "\"status\": 1" status; then
        break
    fi
    sleep 1
done

echo
${SUCCESS} && . $SCRIPTPATH/system_power_reboot.sh

echo ""
echo "Done"
