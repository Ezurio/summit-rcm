#!/bin/bash

################################################################################
#
# antenna_test_sequence.sh
#
# Example script for placing the radio in SISO mode (ANT0 then ANT1) and
# creating an AP connection (for antenna installation validation purposes). When
# finished, the radio is set back to the default SISO mode configuration.
#
################################################################################

source global_settings

# Set PSK for APs
PSK="12345678"

login () {
    echo "Logging in..."

    ${CURL_APP} -s --header "Content-Type: application/json" \
        --request POST \
        --data '{"username":"'"${SUMMIT_RCM_USERNAME}"'","password":"'"${SUMMIT_RCM_PASSWORD}"'"}' \
        --insecure ${URL}/login \
        -c cookie \
        -b cookie \
    | ${JQ_APP}

    echo "Login complete"
    echo ""
}

find_wlan0_mac_address () {
    echo "Retrieving wlan0 MAC address..."

    network_interface=`${CURL_APP} -s --location \
        --request GET ${URL}/networkInterface?name=wlan0 \
        -b cookie -c cookie --insecure \
    | ${JQ_APP}`

    WLAN_MAC=`echo $network_interface | tr '\n' ' ' | sed -nr 's/.*"PermHwAddress": "([a-fA-F0-9\:]*)",.*/\1/p'`

    echo "Found wlan0 MAC address as '${WLAN_MAC}'"
    echo ""
}

set_radio_siso_mode () {
    echo "Setting radio SISO mode to $1..."

    ${CURL_APP} -s --location \
        --request PUT "${URL}/radioSISOMode?SISO_mode=$1" \
        -b cookie -c cookie --insecure \
        --data-raw '' \
    | ${JQ_APP}

    echo "Radio SISO mode now set to $1"
    echo ""
}

create_ap_connection () {
    SSID="hotspot_${WLAN_MAC}_$1"
    echo "Creating connection with SSID '${SSID}'..."

    ${CURL_APP} -s --header "Content-Type: application/json" \
        --request POST \
        ${URL}/connection \
        -b cookie -c cookie --insecure \
        --data '{
            "connection": {
                "autoconnect": 1,
                "id": "'"${SSID}"'",
                "interface-name": "wlan0",
                "type": "802-11-wireless",
                "uuid": ""
            },
            "802-11-wireless": {
                "mode": "ap",
                "ssid": "'"${SSID}"'"
            },
            "ipv4": {
                "method": "shared"
            },
            "802-11-wireless-security": {
                "key-mgmt": "wpa-psk",
                "psk":  "'"${PSK}"'"
            }
        }'\
    | ${JQ_APP}

    connections=`${CURL_APP} -s --header "Content-Type: application/json" \
        --request GET \
        ${URL}/connections \
        -b cookie -c cookie --insecure \
    | ${JQ_APP}`

    CONNECTION_UUID=`echo $connections | tr '\n' ' ' | sed -nr "s/.*\"(.*)\": \{\s*\"activated\": .,\s*\"id\": \"${SSID}\".*/\1/p"`
    echo "Connection created"
    echo "> SSID: ${SSID}"
    echo "> UUID: ${CONNECTION_UUID}"
    echo ""
}

activate_connection () {
    echo "Activating connection with UUID $1..."

    ${CURL_APP} -s --header "Content-Type: application/json" \
        --request PUT \
        ${URL}/connection \
        -b cookie -c cookie --insecure \
        --data '{
            "uuid": "'"$1"'",
            "activate" : '1'
        } '\
    | ${JQ_APP}

    echo "Connection activated"
    echo ""
}

delay_for_ap_detection () {
    echo "Sleeping for $1 seconds to allow for AP detection..."

    sleep $1

    echo "Sleep complete"
    echo ""
}

remove_connection () {
    echo "Removing connection with UUID $1..."

    ${CURL_APP}  \
        -s --request DELETE ${URL}/connection?uuid=$1 \
        -b cookie -c cookie --insecure \
    | ${JQ_APP}

    echo "Connection deleted"
    echo ""
}

# Login to the REST API
login

# Find wlan0 MAC address
find_wlan0_mac_address

# Configure the SOM60's radio for ANT0 (SISO_MODE=1)
set_radio_siso_mode 1

# Create ANT0 connection
create_ap_connection "ANT0"

# Activate the ANT0 connection
activate_connection $CONNECTION_UUID

# Sleep to allow for detecting SSID
delay_for_ap_detection 30

# Delete ANT0 connection
remove_connection $CONNECTION_UUID

# Configure the SOM60's radio for ANT1 (SISO_MODE=2)
set_radio_siso_mode 2

# Create ANT1 connection
create_ap_connection "ANT1"

# Activate the ANT1 connection
activate_connection $CONNECTION_UUID

# Sleep to allow for detecting SSID
delay_for_ap_detection 30

# Delete ANT1 connection
remove_connection $CONNECTION_UUID

# Revert to default SISO mode (SISO_MODE=-1)
set_radio_siso_mode -1

echo "Done"
echo -e "\n"
