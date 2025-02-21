##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings

echo -e "\n========================="
echo "Get radio SISO mode"

${CURL_APP} -s --location \
    --request GET "${URL}/radioSISOMode" \
    ${AUTH_OPT} \
| ${JQ_APP}
echo -e "\n"

