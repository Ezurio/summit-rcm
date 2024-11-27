##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

# Webserver Log Levels:
# - critical
# - error (default)
# - warning
# - info
# - debug
# - trace
WEBSERVER_LOG_LEVEL="${WEBSERVER_LOG_LEVEL:-"error"}"

source ../global_settings

echo -e "\n========================="
echo "Set webserver log level"

${CURL_APP} -s --location \
    --request PUT ${URL}/logWebserver \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data '{"webserverLogLevel":"'"${WEBSERVER_LOG_LEVEL}"'"}' \
| ${JQ_APP}

echo -e "\n"

