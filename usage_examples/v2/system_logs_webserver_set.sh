#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

source ../global_settings

# Webserver Log Levels:
# - critical
# - error (default)
# - warning
# - info
# - debug
# - trace
WEBSERVER_LOG_LEVEL="${WEBSERVER_LOG_LEVEL:-"error"}"

echo "========================="
echo "Set webserver log level"
echo "========================="
echo

echo "Webserver Log Level: ${WEBSERVER_LOG_LEVEL}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\n" \
    --request PUT ${URL}/api/v2/system/logs/webserver \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data '{
        "webserverLogLevel": "'"${WEBSERVER_LOG_LEVEL}"'"
    }' \
    -o >(${JQ_APP})

wait
