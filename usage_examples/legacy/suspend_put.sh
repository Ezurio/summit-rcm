##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings

echo -e "\n\n========================="
echo "Suspend"
${CURL_APP} -s --location --request PUT ${URL}/suspend \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure\
    --data-raw ''\
| ${JQ_APP}


echo -e "\n"
