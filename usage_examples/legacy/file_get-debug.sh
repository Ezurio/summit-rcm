##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings

echo -e "\n========================="
echo "Get config"

${CURL_APP} -s --location \
    --request GET "${URL}/file?type=debug" \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data-raw '' \
    --output debug.encrypt

echo -e "\ndebug.encrypt file downloaded. To decrypt:"
echo "openssl smime -decrypt -in debug.encrypt -recip server.crt -inkey server.key -out debug.zip --inform DER"
