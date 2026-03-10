##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2026 Ezurio LLC.
##
source ../global_settings

echo -e "\n========================="
echo "POST config"

${CURL_APP} -s --location \
    --request POST "${URL}/file?type=config&password=test" \
    ${AUTH_OPT} \
    --form 'file=@"config.zip"' \
| ${JQ_APP}
echo -e "\nconfig.zip uploaded. Reboot to take effect"


