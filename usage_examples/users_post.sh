USR="${USR:-"test"}"
PASSWORD="${PASSWORD:-12345678}"
PERMISSIONS="${PERMISSIONS:-"status_networking networking_connections networking_edit networking_activate networking_ap_activate networking_delete networking_scan networking_certs logging help_version system_datetime system_swupdate system_password system_advanced system_positioning system_reboot "}"

source global_settings

echo -e "\n========================="
echo "Add user"

${CURL_APP} -s --location \
    --request POST ${URL}/users \
    --header "Content-Type: application/json" \
    -b cookie -c cookie --insecure \
    --data '{"username":"'"${USR}"'", "password":"'"${PASSWORD}"'", "permission":"'"${PERMISSIONS}"'"}' \
| ${JQ_APP}
echo -e "\n"

