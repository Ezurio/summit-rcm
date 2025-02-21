##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
USR="${USR:-"test"}"

source ../global_settings

echo -e "\n========================="
echo "del user"

${CURL_APP} -s --location \
    --request DELETE ${URL}/users?username=${USR} \
    --header "Content-Type: application/json" \
    ${AUTH_OPT} \
    | ${JQ_APP}

echo -e "\n"

