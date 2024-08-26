##
## SPDX-License-Identifier: LicenseRef-Ezurio-Clause
## Copyright (C) 2024 Ezurio LLC.
##
source ../global_settings

echo -e "\n========================="
echo "Upload signed device server certificate"

REQUEST_URL="${URL}/certificateProvisioning"

${CURL_APP} -s --location \
    --request PUT "${REQUEST_URL}" \
    -b cookie -c cookie --insecure \
    --form 'certificate=@"'"${FILE}"'"' \
| ${JQ_APP}

echo -e "\n"
