CONNECTION_NAME=EAP_TLS_CA_CERT

source global_settings

echo ""
echo "========================="
echo "Modify connection"
${CURL_APP} -s --header "Content-Type: application/json" \
    --request POST \
    ${URL}/connection \
    -b cookie -c cookie --insecure \
    --data '{
    "connection": {
      "id": "br-slave-wlan0",
      "uuid": "bd89b41c-5688-3e79-8353-f7391d8e5ce9",
      "autoconnect" : 0
    },
    "802-11-wireless": {
      "band": "a",
      "channel": 36,
      "channel-width" : 80,
      "hidden" : 1,
      "ssid": "Ssid"
    },
    "802-11-wireless-security": {
      "group": "ccmp",
      "key-mgmt": "wpa-psk",
      "pairwise": "ccmp",
      "proto" : "rsn",
      "pmf" : 1,
      "psk" : "PASSWORD"
    }
  } '\
        | ${JQ_APP}

echo -e "\n"


