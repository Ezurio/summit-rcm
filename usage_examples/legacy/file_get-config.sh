##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings

echo -e "\n========================="
echo "Get config"

${CURL_APP} -s --location \
    --request GET "${URL}/file?type=config&password=test" \
    --header "Content-Type: application/json" \
    ${AUTH_OPT} \
    --data-raw '' \
    --output config.zip

echo "config.zip downloaded"
echo -e "\n"

