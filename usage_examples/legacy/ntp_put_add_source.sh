##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings

echo -e "\n========================="
echo "Add NTP sources"

${CURL_APP} -s --location \
    --request PUT ${URL}/ntp/addSource \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data '{
        "sources": [
            "time.nist.gov"
        ]
    }'\
| ${JQ_APP}
echo -e "\n"

