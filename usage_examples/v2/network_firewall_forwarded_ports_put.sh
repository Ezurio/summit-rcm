#! /bin/bash

source ../global_settings

echo "========================="
echo "Update forwarded ports"
echo "========================="
echo

echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request PUT ${URL}/api/v2/network/firewall/forwardedPorts \
    -b cookie -c cookie --insecure \
    --header "Content-Type: application/json" \
    --data '[
        {
            "port": "1234",
            "protocol": "tcp",
            "toport": "1234",
            "toaddr": "8.8.8.8",
            "ipVersion": "ipv4"
        }
    ]' \
    -o >(${JQ_APP})

wait
