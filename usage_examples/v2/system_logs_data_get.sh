#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

source ../global_settings

LOG_TYPE="${LOG_TYPE:-"All"}"
PRIORITY="${PRIORITY:-6}"
DAYS="${DAYS:-0}"
HOURS="${HOURS:-0}"

echo "========================="
echo "Get log data"
echo "========================="
echo

echo "Log Type: ${LOG_TYPE}"
echo "Priority: ${PRIORITY}"
echo "Days: ${DAYS}"
echo "Hours: ${HOURS}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\n" \
    --request GET "${URL}/api/v2/system/logs/data?type=${LOG_TYPE}&priority=${PRIORITY}&days=${DAYS}&hours=${HOURS}" \
    ${AUTH_OPT} \
    -o >(${JQ_APP})

wait
