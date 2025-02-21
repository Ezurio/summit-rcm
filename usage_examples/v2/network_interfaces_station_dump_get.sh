#! /bin/bash
##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2025 Ezurio LLC.
##

##############################################
#                                            #
# NOTE: The station dump information is not  #
# guaranteed to be always correct.           #
#                                            #
##############################################

NAME="${NAME:-"wlan0"}"

source ../global_settings

echo "========================="
echo "Get network interface station dump by name"
echo "========================="
echo

echo "Interface Name: ${NAME}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\nResponse:\n" \
    --request GET ${URL}/api/v2/network/interfaces/${NAME}/stationDump \
    ${AUTH_OPT} \
    -o >(${JQ_APP})

wait
