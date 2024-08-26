##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings
ARCHIVE_PASSWORD="${ARCHIVE_PASSWORD:-"1234"}"

echo "========================="
echo "Import connections"
${CURL_APP} -s --location \
    --request PUT \
    "${URL}/files?type=network&password=${ARCHIVE_PASSWORD}" \
    -b cookie -c cookie --insecure \
    --form 'archive=@"connections.zip"' \
| ${JQ_APP}

echo -e "\n"
