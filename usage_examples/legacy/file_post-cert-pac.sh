##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##

#FILE=user2.pem

source ../global_settings

echo ""
echo "========================="
echo "Upload cert file for Network Manager"
${CURL_APP} -s --request POST \
    ${URL}/file \
    -b cookie -c cookie --insecure \
    --form 'type="cert"' \
    --form 'file=@"'"${FILE}"'"'

echo -e "\n"


