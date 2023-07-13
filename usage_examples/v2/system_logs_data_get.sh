#! /bin/bash

source ../global_settings

LOG_TYPE="${LOG_TYPE:-"All"}"
PRIORITY="${PRIORITY:-6}"
DAYS="${DAYS:--1}"

echo "========================="
echo "Get log data"
echo "========================="
echo

echo "Log Type: ${LOG_TYPE}"
echo "Priority: ${PRIORITY}"
echo "Days: ${DAYS}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\n" \
    --request GET "${URL}/api/v2/system/logs/data?type=${LOG_TYPE}&priority=${PRIORITY}&days=${DAYS}" \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
