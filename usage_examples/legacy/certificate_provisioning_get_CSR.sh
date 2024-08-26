##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings

CONFIG_FILE="${CONFIG_FILE:-"certificate_provisioning_CSR.cnf"}"
OPENSSL_KEY_GEN_ARGS="${OPENSSL_KEY_GEN_ARGS:-""}"

echo -e "\n========================="
echo "Get device server CSR using the specified configuration file"
echo
echo "CSR creation configuration file: ${CONFIG_FILE}"
echo "OpenSSL key generation args: ${OPENSSL_KEY_GEN_ARGS}"

REQUEST_URL="${URL}/certificateProvisioning"

${CURL_APP} -s --location \
    --request POST "${REQUEST_URL}" \
    -b cookie -c cookie --insecure \
    --form 'configFile=@"'"${CONFIG_FILE}"'"' \
    --form 'opensslKeyGenArgs="'"${OPENSSL_KEY_GEN_ARGS}"'"' \
    --output dev.csr

echo -e "\n"
