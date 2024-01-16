#! /bin/bash

CONFIG_FILE="${CONFIG_FILE:-"certificate_provisioning_CSR.cnf"}"
OPENSSL_KEY_GEN_ARGS="${OPENSSL_KEY_GEN_ARGS:-""}"

source ../global_settings

echo "========================="
echo "Get device server CSR using the specified configuration file"
echo "========================="
echo "CSR creation configuration file: ${CONFIG_FILE}"
echo "OpenSSL key generation args: ${OPENSSL_KEY_GEN_ARGS}"
echo -n "Status Code: "

curl -s --location \
    -w "%{http_code}\n" \
    --request POST ${URL}/api/v2/system/certificateProvisioning \
    -b cookie -c cookie --insecure \
    --form 'configFile=@"'"${CONFIG_FILE}"'"' \
    --form 'opensslKeyGenArgs="'"${OPENSSL_KEY_GEN_ARGS}"'"' \
    --output dev.csr

wait
