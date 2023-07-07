#! /bin/bash

# Statuses:
# 0 -> Updated
# 1 -> Fail
# 2 -> Not updating
# 5 -> Updating
DESIRED_STATUS="${DESIRED_STATUS:-5}"
FIRMWARE_URL="${FIRMWARE_URL:-""}"
IMAGE="${IMAGE:-"full"}"

SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

. ${SCRIPTPATH}/../global_settings

echo "========================="
echo "Set current update status"
echo "========================="
echo

echo "Desired update status: ${DESIRED_STATUS}"
echo "Firmware URL: ${FIRMWARE_URL}"
echo "Image: ${IMAGE}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/system/update \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data '{
        "status": '${DESIRED_STATUS}',
        "url": "'"${FIRMWARE_URL}"'",
        "image": "'"${IMAGE}"'"
    }' \
    -o >(${JQ_APP})

wait
