##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings


echo -e "\n========================="
echo "Delete virtual networkinterface"

${CURL_APP} -s \
    --request DELETE ${URL}/networkInterfaces?interface=wlan1 \
    -b cookie -c cookie --insecure \
| ${JQ_APP}

echo -e "\n"

