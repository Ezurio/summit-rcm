UUID="${UUID:-"a760e87e-e23a-4ea6-81f9-c4e29052db27"}"
ACTIVATE="${ACTIVATE:-1}"

source ../global_settings

echo ""
echo "========================="
echo "Activate/Deactivate connection"
${CURL_APP} -s --header "Content-Type: application/json" \
    --request PUT \
    ${URL}/connection \
    -b cookie -c cookie --insecure \
    --data '{
      "uuid": "'"${UUID}"'",
      "activate" : '${ACTIVATE}'
  } '\
        | ${JQ_APP}

echo -e "\n"


