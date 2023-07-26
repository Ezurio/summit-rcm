#! /bin/bash

SOURCE_ADDRESS="${SOURCE_ADDRESS:-"time.nist.gov"}"

source ../global_settings

echo "========================="
echo "Get NTP source by address"
echo "========================="
echo


echo "Source Address: ${SOURCE_ADDRESS}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request GET ${URL}/api/v2/system/datetime/ntp/${SOURCE_ADDRESS} \
    -b cookie -c cookie --insecure \
    -o >(${JQ_APP})

wait
