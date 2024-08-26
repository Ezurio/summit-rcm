##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings

echo -e "\n========================="
echo "POST config"

${CURL_APP} -s --location \
    --request POST "${URL}/file" \
    --insecure \
    -b cookie -c cookie \
    --form 'type="config"' \
    --form 'file=@"config.zip"' \
    --form 'password="test"' \
| ${JQ_APP}
echo -e "\nconfig.zip uploaded. Reboot to take effect"


