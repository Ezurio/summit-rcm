<!--
SPDX-License-Identifier: LicenseRef-Ezurio-Clause
Copyright (C) 2024 Ezurio LLC.
-->
# Summit RCM Legacy (deprecated) API
This is a set of scripts which can be used for testing/verification and examples of usage for the various RESTful APIs.

These scripts and testing are verified on Ubuntu 24.04, but the curl commands should work on other platforms.  The global_settings will likely only work on Linux variants without modifications.

The intent is for settings that remain consistent amongst all the scripts can be stored in the global_settings file.  The ip address of the Device Under Test (DUT) can be supplied with the variable IPADDR and this will be stored automatically.  Any other changes to global_settings must be manually modified.

The global_settings in my setup are set for after the initial password change.  Therefore, for the initial login, I will supply the original password as a parameter.

Finally, a word about the cookie file.  The login script will save a cookie file over an existing cookie even if the login fails. This could cause you to lose the session id and get errors when trying other commands, including logging out.  To prevent this, you can make a copy of your cookie file with the appropriate command for your system.  If the issue does occur, you can wait for your session to expire (about 10 minutes), restart the summit-rcm.service from the console login, or reboot the DUT. This condition presents itself as a HTTP 401 (Unauthorized) response.

NOTE: This is not an issue if the Summit RCM "Allow multiple sessions per user" setting is enabled.

# Determine the IP address of the DUT *(commands not shown)*

# Login / Logout / change password
Assuming an IPADDR has never been set, when the first attempt to use any script, you will get an error.  Example:

    # SUMMIT_RCM_PASSWORD=summit ./login_post.sh
    IPADDR variable needs to be set.

Supply the IPADDR and results show successful login with a change password required message:

    # IPADDR=192.168.1.233 SUMMIT_RCM_PASSWORD=summit ./login_post.sh
    =====
    Login
    {
      "SDCERR": 0,
      "REDIRECT": 1,
      "PERMISSION": "",
      "InfoMsg": "Password change required"
    }

Note that the login is successful (and therefore the cookie is valid) but a password change is required. The current cookie file is used in the users_put-changepw.sh script:

    # ./users_put-changepw.sh

    =====
    Change password
    {
      "SDCERR": 0,
      "REDIRECT": 1,
      "InfoMsg": "password changed"
    }

Logout and login with new password:
    # ./login_delete.sh

    ======
    logout
    {
      "SDCERR": 0,
      "InfoMsg": "user root logged out"
    }

    # ./login.sh

    =====
    Login
    {
      "SDCERR": 0,
      "REDIRECT": 0,
      "PERMISSION": "status_networking networking_connections networking_edit networking_activate networking_ap_activate networking_delete networking_scan networking_certs logging help_version system_datetime system_swupdate system_password system_advanced system_positioning system_reboot ",
      "InfoMsg": "User logged in"
    }

# Network Status

./networkStatus_get.sh
=========================
    network status
    {
      "SDCERR": 0,
      "InfoMsg": "",
      "status": {
        "eth0": {
          "status": {
            "State": 70,
            "StateText": "IP Config",
            "Mtu": 1500,
            "DeviceType": 1,
            "DeviceTypeText": "Ethernet"
          },
          "wired": {
            "HwAddress": "3E:5C:3C:43:3D:F4",
            "PermHwAddress": "3E:5C:3C:43:3D:F4",
            "Speed": 100,
            "Carrier": true
          }
        },
        "usb0": {
          "status": {
            "State": 20,
            "StateText": "Unavailable",
            "Mtu": 1500,
            "DeviceType": 1,
            "DeviceTypeText": "Ethernet"
          },
          "wired": {
            "HwAddress": "DE:AD:BE:EF:00:00",
            "PermHwAddress": "",
            "Speed": 0,
            "Carrier": false
          }
        },
        "wlan0": {
          "status": {
            "State": 50,
            "StateText": "Config",
            "Mtu": 1500,
            "DeviceType": 2,
            "DeviceTypeText": "Wi-Fi"
          },
          "wireless": {
            "Bitrate": 0,
            "HwAddress": "C0:EE:40:64:54:18",
            "PermHwAddress": "C0:EE:40:64:54:18",
            "Mode": 2,
            "LastScan": 34463
          },
          "RegDomain": "US"
        },
        "p2p-dev-wlan0": {
          "status": {
            "State": 30,
            "StateText": "Disconnected",
            "Mtu": 0,
            "DeviceType": 30,
            "DeviceTypeText": "WiFi P2P"
          }
        }
      },
      "devices": 4
    }

# Connections

    # ./connections_get.sh
    =========================
    Connections
    {
      "SDCERR": 0,
      "connections": {
        "f93578c1-d309-4103-8554-fc1982ccda02": {
          "id": "static-usb0",
          "activated": 0
        },
        "1f690a78-c4ab-4337-9f8a-005c805cf4b6": {
          "id": "bill",
          "activated": 1
        },
        "1f51b6e8-fe7c-36a5-ae5b-24c7130f2b2a": {
          "id": "Wired connection 1",
          "activated": 0
        }
      },
      "InfoMsg": "",
      "length": 3
    }

# Create connection
this will create all the example connections in this package:
(The InfoMsg string will be changed to indicate the connection was created

    # for connection in connection_post_*; do echo $connection; ./$connection; done
    connection_post_EAP-TLS-ca-cert.sh
    EAP TLS CA cert

    =========================
    Create connection
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    connection_post_EAP-TLS-no-cert.sh
    EAP TLS w/o CA cert

    =========================
    Create connection
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    connection_post_EAP-TTLS-CA-cert.sh
    EAP TLS w/o cert

    =========================
    Create connection
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    connection_post_EAP-TTLS-no-cert.sh
    EAP TTLS w/o CA cert

    =========================
    Create connection
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    connection_post_PEAP-GTC-CA-cert.sh

    PEAP GTC w/CA cert

    =========================
    Create connection
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    connection_post_PEAP-GTC-NO-cert.sh

    PEAP GTC w/o CA cert

    =========================
    Create connection
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    connection_post_PEAP-MSCHAPv2-CA-cert.sh

    PEAP MSCHAPv2 w/CA cert

    =========================
    Create connection
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    connection_post_PEAP-MSCHAPv2-no-cert.sh

    PEAP MSCHAPv2 w/o CA cert

    =========================
    Create connection
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }

## created connections:

    ./connections_get.sh
    =========================
    Connections
    {
      "SDCERR": 0,
      "connections": {
        "f93578c1-d309-4103-8554-fc1982ccda02": {
          "id": "static-usb0",
          "activated": 0
        },
        "1f690a78-c4ab-4337-9f8a-005c805cf4b6": {
          "id": "bill",
          "activated": 1
        },
        "1f51b6e8-fe7c-36a5-ae5b-24c7130f2b2a": {
          "id": "Wired connection 1",
          "activated": 0
        },
        "a7b534f2-a739-44d7-a8d3-6bb62f5fee65": {
          "id": "EAP_TLS_CA_CERT",
          "activated": 0
        },
        "44a2ce9c-12a4-4205-90f2-0025148a82da": {
          "id": "EAP_TLS_NO_CA_CERT",
          "activated": 0
        },
        "43340c99-d518-44a4-8c87-394e4b931fdd": {
          "id": "EAP_TTLS_CA_CERT",
          "activated": 0
        },
        "dd30b4ef-3870-46cf-b6ef-02e064ec7192": {
          "id": "EAP_TTLS_NO_CA_CERT",
          "activated": 0
        },
        "e39ae926-2dde-455a-9645-953a22e2035a": {
          "id": "PEAP_GTC_CA_CERT",
          "activated": 0
        },
        "e4eea0ae-9299-48d5-a879-a1cdb10a1425": {
          "id": "PEAP_GTC_NO_CA_CERT",
          "activated": 0
        },
        "e29e0e05-a7f4-41c0-8d29-aa9a00496de1": {
          "id": "PEAP_MSCHAPv2_CA_CERT",
          "activated": 0
        },
        "3bc8bea2-446f-4f03-878d-1426e28540ae": {
          "id": "PEAP_MSCHAPv2_NO_CA_CERT",
          "activated": 0
        }
      },
      "InfoMsg": "",
      "length": 11
    }

## examine new connections:
### *this requires the jq tool.  Install it before trying*

    # for UUID in `JQ_APP=tee ./connections_get.sh |\
             jq -R 'fromjson? |\
             select(type == "object")'|\
             jq '.connections | [ to_entries[] | {uuid: .key} + .value]'|\
             jq '[ .[] | select(.id|test(".*CERT.*")) ]' |\
             jq '.[].uuid' |
             tr -d \"`;
             do
                 UUID=${UUID} ./connection_get.sh;
             done
    a7b534f2-a739-44d7-a8d3-6bb62f5fee65

    =========================
    Get connection
    {
      "SDCERR": 0,
      "InfoMsg": "",
      "connection": {
        "connection": {
          "autoconnect": false,
          "id": "EAP_TLS_CA_CERT",
          "interface-name": "wlan0",
          "permissions": [],
          "type": "802-11-wireless",
          "uuid": "a7b534f2-a739-44d7-a8d3-6bb62f5fee65",
          "zone": "trusted"
        },
        "802-11-wireless": {
          "bgscan": "summit:5:-64:30",
          "mac-address-blacklist": [],
          "mode": "infrastructure",
          "security": "802-11-wireless-security",
          "ssid": "EAP_TLS_CA_CERT"
        },
        "802-11-wireless-security": {
          "key-mgmt": "wpa-eap",
          "pairwise": "ccmp",
          "proactive-key-caching": "1",
          "proto": "rsn"
        },
        "802-1x": {
          "ca-cert": "SystestCA.cer",
          "client-cert": "None",
          "eap": "tls",
          "identity": "user1",
          "private-key": "user1.pfx",
          "phase2-ca-cert": null,
          "phase2-client-cert": null,
          "phase2-private-key": null
        },
        "ipv4": {
          "address-data": [],
          "addresses": [],
          "dns": [],
          "dns-search": [],
          "method": "auto",
          "route-data": [],
          "routes": []
        },
        "ipv6": {
          "address-data": [],
          "addresses": [],
          "dns": [],
          "dns-search": [],
          "method": "auto",
          "route-data": [],
          "routes": []
        },
        "proxy": {}
      }
    }


    44a2ce9c-12a4-4205-90f2-0025148a82da

    =========================
    Get connection
    {
      "SDCERR": 0,
      "InfoMsg": "",
      "connection": {
        "connection": {
          "autoconnect": false,
          "id": "EAP_TLS_NO_CA_CERT",
          "interface-name": "wlan0",
          "permissions": [],
          "type": "802-11-wireless",
          "uuid": "44a2ce9c-12a4-4205-90f2-0025148a82da",
          "zone": "trusted"
        },
        "802-11-wireless": {
          "bgscan": "summit:5:-64:30",
          "mac-address-blacklist": [],
          "mode": "infrastructure",
          "security": "802-11-wireless-security",
          "ssid": "EAP_TLS_NO_CA_CERT"
        },
        "802-11-wireless-security": {
          "key-mgmt": "wpa-eap",
          "pairwise": "ccmp",
          "proactive-key-caching": "1",
          "proto": "rsn"
        },
        "802-1x": {
          "client-cert": "None",
          "eap": "tls",
          "identity": "user1",
          "private-key": "user1.pfx",
          "ca-cert": null,
          "phase2-ca-cert": null,
          "phase2-client-cert": null,
          "phase2-private-key": null
        },
        "ipv4": {
          "address-data": [],
          "addresses": [],
          "dns": [],
          "dns-search": [],
          "method": "auto",
          "route-data": [],
          "routes": []
        },
        "ipv6": {
          "address-data": [],
          "addresses": [],
          "dns": [],
          "dns-search": [],
          "method": "auto",
          "route-data": [],
          "routes": []
        },
        "proxy": {}
      }
    }


    43340c99-d518-44a4-8c87-394e4b931fdd

    =========================
    Get connection
    {
      "SDCERR": 0,
      "InfoMsg": "",
      "connection": {
        "connection": {
          "autoconnect": false,
          "id": "EAP_TTLS_CA_CERT",
          "interface-name": "wlan0",
          "permissions": [],
          "type": "802-11-wireless",
          "uuid": "43340c99-d518-44a4-8c87-394e4b931fdd",
          "zone": "trusted"
        },
        "802-11-wireless": {
          "mac-address-blacklist": [],
          "mode": "infrastructure",
          "security": "802-11-wireless-security",
          "ssid": "EAP_TTLS_CA_CERT"
        },
        "802-11-wireless-security": {
          "key-mgmt": "wpa-eap",
          "pairwise": "ccmp",
          "proactive-key-caching": "1",
          "proto": "rsn"
        },
        "802-1x": {
          "anonymous-identity": "anonNAME",
          "ca-cert": "SystestCA.cer",
          "client-cert": "None",
          "eap": "ttls",
          "identity": "user1",
          "phase2-autheap": "gtc",
          "private-key": null,
          "phase2-ca-cert": null,
          "phase2-client-cert": null,
          "phase2-private-key": null
        },
        "ipv4": {
          "address-data": [],
          "addresses": [],
          "dns": [],
          "dns-search": [],
          "method": "auto",
          "route-data": [],
          "routes": []
        },
        "ipv6": {
          "address-data": [],
          "addresses": [],
          "dns": [],
          "dns-search": [],
          "method": "auto",
          "route-data": [],
          "routes": []
        },
        "proxy": {}
      }
    }


    dd30b4ef-3870-46cf-b6ef-02e064ec7192

    =========================
    Get connection
    {
      "SDCERR": 0,
      "InfoMsg": "",
      "connection": {
        "connection": {
          "autoconnect": false,
          "id": "EAP_TTLS_NO_CA_CERT",
          "interface-name": "wlan0",
          "permissions": [],
          "type": "802-11-wireless",
          "uuid": "dd30b4ef-3870-46cf-b6ef-02e064ec7192",
          "zone": "trusted"
        },
        "802-11-wireless": {
          "mac-address-blacklist": [],
          "mode": "infrastructure",
          "security": "802-11-wireless-security",
          "ssid": "EAP_TTLS_NO_CA_CERT"
        },
        "802-11-wireless-security": {
          "key-mgmt": "wpa-eap",
          "pairwise": "ccmp",
          "proactive-key-caching": "1",
          "proto": "rsn"
        },
        "802-1x": {
          "anonymous-identity": "anonNAME",
          "client-cert": "None",
          "eap": "ttls",
          "identity": "user1",
          "phase2-autheap": "gtc",
          "ca-cert": null,
          "private-key": null,
          "phase2-ca-cert": null,
          "phase2-client-cert": null,
          "phase2-private-key": null
        },
        "ipv4": {
          "address-data": [],
          "addresses": [],
          "dns": [],
          "dns-search": [],
          "method": "auto",
          "route-data": [],
          "routes": []
        },
        "ipv6": {
          "address-data": [],
          "addresses": [],
          "dns": [],
          "dns-search": [],
          "method": "auto",
          "route-data": [],
          "routes": []
        },
        "proxy": {}
      }
    }


    e39ae926-2dde-455a-9645-953a22e2035a

    =========================
    Get connection
    {
      "SDCERR": 0,
      "InfoMsg": "",
      "connection": {
        "connection": {
          "autoconnect": false,
          "id": "PEAP_GTC_CA_CERT",
          "interface-name": "wlan0",
          "permissions": [],
          "type": "802-11-wireless",
          "uuid": "e39ae926-2dde-455a-9645-953a22e2035a",
          "zone": "trusted"
        },
        "802-11-wireless": {
          "mac-address-blacklist": [],
          "mode": "infrastructure",
          "security": "802-11-wireless-security",
          "ssid": "PEAP_GTC_CA_CERT"
        },
        "802-11-wireless-security": {
          "key-mgmt": "wpa-eap",
          "pairwise": "ccmp",
          "proactive-key-caching": "1",
          "proto": "rsn"
        },
        "802-1x": {
          "ca-cert": "SystestCA.cer",
          "client-cert": "None",
          "eap": "peap",
          "identity": "user1",
          "phase2-autheap": "gtc",
          "private-key": null,
          "phase2-ca-cert": null,
          "phase2-client-cert": null,
          "phase2-private-key": null
        },
        "ipv4": {
          "address-data": [],
          "addresses": [],
          "dns": [],
          "dns-search": [],
          "method": "auto",
          "route-data": [],
          "routes": []
        },
        "ipv6": {
          "address-data": [],
          "addresses": [],
          "dns": [],
          "dns-search": [],
          "method": "auto",
          "route-data": [],
          "routes": []
        },
        "proxy": {}
      }
    }


    e4eea0ae-9299-48d5-a879-a1cdb10a1425

    =========================
    Get connection
    {
      "SDCERR": 0,
      "InfoMsg": "",
      "connection": {
        "connection": {
          "autoconnect": false,
          "id": "PEAP_GTC_NO_CA_CERT",
          "interface-name": "wlan0",
          "permissions": [],
          "type": "802-11-wireless",
          "uuid": "e4eea0ae-9299-48d5-a879-a1cdb10a1425",
          "zone": "trusted"
        },
        "802-11-wireless": {
          "mac-address-blacklist": [],
          "mode": "infrastructure",
          "security": "802-11-wireless-security",
          "ssid": "PEAP_GTC_NO_CA_CERT"
        },
        "802-11-wireless-security": {
          "key-mgmt": "wpa-eap",
          "pairwise": "ccmp",
          "proactive-key-caching": "1",
          "proto": "rsn"
        },
        "802-1x": {
          "client-cert": "None",
          "eap": "peap",
          "identity": "user1",
          "phase2-autheap": "gtc",
          "ca-cert": null,
          "private-key": null,
          "phase2-ca-cert": null,
          "phase2-client-cert": null,
          "phase2-private-key": null
        },
        "ipv4": {
          "address-data": [],
          "addresses": [],
          "dns": [],
          "dns-search": [],
          "method": "auto",
          "route-data": [],
          "routes": []
        },
        "ipv6": {
          "address-data": [],
          "addresses": [],
          "dns": [],
          "dns-search": [],
          "method": "auto",
          "route-data": [],
          "routes": []
        },
        "proxy": {}
      }
    }


    e29e0e05-a7f4-41c0-8d29-aa9a00496de1

    =========================
    Get connection
    {
      "SDCERR": 0,
      "InfoMsg": "",
      "connection": {
        "connection": {
          "autoconnect": false,
          "id": "PEAP_MSCHAPv2_CA_CERT",
          "interface-name": "wlan0",
          "permissions": [],
          "type": "802-11-wireless",
          "uuid": "e29e0e05-a7f4-41c0-8d29-aa9a00496de1",
          "zone": "trusted"
        },
        "802-11-wireless": {
          "mac-address-blacklist": [],
          "mode": "infrastructure",
          "security": "802-11-wireless-security",
          "ssid": "PEAP_MSCHAPv2_CA_CERT"
        },
        "802-11-wireless-security": {
          "key-mgmt": "wpa-eap",
          "pairwise": "ccmp",
          "proactive-key-caching": "1",
          "proto": "rsn"
        },
        "802-1x": {
          "ca-cert": "SystestCA.cer",
          "client-cert": "None",
          "eap": "peap",
          "identity": "user1",
          "phase2-autheap": "mschapv2",
          "private-key": null,
          "phase2-ca-cert": null,
          "phase2-client-cert": null,
          "phase2-private-key": null
        },
        "ipv4": {
          "address-data": [],
          "addresses": [],
          "dns": [],
          "dns-search": [],
          "method": "auto",
          "route-data": [],
          "routes": []
        },
        "ipv6": {
          "address-data": [],
          "addresses": [],
          "dns": [],
          "dns-search": [],
          "method": "auto",
          "route-data": [],
          "routes": []
        },
        "proxy": {}
      }
    }


    3bc8bea2-446f-4f03-878d-1426e28540ae

    =========================
    Get connection
    {
      "SDCERR": 0,
      "InfoMsg": "",
      "connection": {
        "connection": {
          "autoconnect": false,
          "id": "PEAP_MSCHAPv2_NO_CA_CERT",
          "interface-name": "wlan0",
          "permissions": [],
          "type": "802-11-wireless",
          "uuid": "3bc8bea2-446f-4f03-878d-1426e28540ae",
          "zone": "trusted"
        },
        "802-11-wireless": {
          "mac-address-blacklist": [],
          "mode": "infrastructure",
          "security": "802-11-wireless-security",
          "ssid": "PEAP_MSCHAPv2_NO_CA_CERT"
        },
        "802-11-wireless-security": {
          "key-mgmt": "wpa-eap",
          "pairwise": "ccmp",
          "proactive-key-caching": "1",
          "proto": "rsn"
        },
        "802-1x": {
          "client-cert": "None",
          "eap": "peap",
          "identity": "user1",
          "phase2-autheap": "mschapv2",
          "ca-cert": null,
          "private-key": null,
          "phase2-ca-cert": null,
          "phase2-client-cert": null,
          "phase2-private-key": null
        },
        "ipv4": {
          "address-data": [],
          "addresses": [],
          "dns": [],
          "dns-search": [],
          "method": "auto",
          "route-data": [],
          "routes": []
        },
        "ipv6": {
          "address-data": [],
          "addresses": [],
          "dns": [],
          "dns-search": [],
          "method": "auto",
          "route-data": [],
          "routes": []
        },
        "proxy": {}
      }
    }

## example showing illegal connection request:

    ./connection_get_no_uuid.sh

    =========================
    Get connection
    {
      "SDCERR": 1,
      "InfoMsg": "no UUID provided"
    }

## delete the new connections we just created
    # for UUID in `JQ_APP=tee ./connections_get.sh |\
              jq -R 'fromjson? |\
              select(type == "object")'|\
              jq '.connections | [ to_entries[] | {uuid: .key} + .value]'|\
              jq '[ .[] | select(.id|test(".*CERT.*")) ]' |\
              jq '.[].uuid' |\
                  tr -d \"`;
              do
                  UUID=${UUID} ./connection_delete.sh
              done
    a7b534f2-a739-44d7-a8d3-6bb62f5fee65
    =========================
    DELETE Connection a7b534f2-a739-44d7-a8d3-6bb62f5fee65
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    44a2ce9c-12a4-4205-90f2-0025148a82da
    =========================
    DELETE Connection 44a2ce9c-12a4-4205-90f2-0025148a82da
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    43340c99-d518-44a4-8c87-394e4b931fdd
    =========================
    DELETE Connection 43340c99-d518-44a4-8c87-394e4b931fdd
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    dd30b4ef-3870-46cf-b6ef-02e064ec7192
    =========================
    DELETE Connection dd30b4ef-3870-46cf-b6ef-02e064ec7192
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    e39ae926-2dde-455a-9645-953a22e2035a
    =========================
    DELETE Connection e39ae926-2dde-455a-9645-953a22e2035a
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    e4eea0ae-9299-48d5-a879-a1cdb10a1425
    =========================
    DELETE Connection e4eea0ae-9299-48d5-a879-a1cdb10a1425
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    e29e0e05-a7f4-41c0-8d29-aa9a00496de1
    =========================
    DELETE Connection e29e0e05-a7f4-41c0-8d29-aa9a00496de1
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    3bc8bea2-446f-4f03-878d-1426e28540ae
    =========================
    DELETE Connection 3bc8bea2-446f-4f03-878d-1426e28540ae
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }

# networkInterfaces

    # ./networkinterfaces_get.sh

    =========================
    Get networkinterfaces
    {
      "SDCERR": 0,
      "InfoMsg": "",
      "interfaces": [
        "eth0",
        "usb0",
        "wlan0",
        "p2p-dev-wlan0"
      ]
    }
# get/put pac/cert files

    # ./files_get.sh

    =========================
    Get list of pac files (supports 'pac' and 'cert')
    []

    # FILE=user1.pem ./file_post-cert-pac.sh

    =========================
    Upload cert file for Network Manager

    # TYPE=cert ./files_get.sh

    =========================
    Get list of cert files (supports 'pac' and 'cert')
    ["user1.pem"]

    # FILE=user1.pac ./file_post-cert-pac.sh

    =========================
    Upload cert file for Network Manager


    # ./files_get.sh

    =========================
    Get list of pac files (supports 'pac' and 'cert')
    ["user1.pac"]

# access points

    # ./accesspoints_put.sh

    =========================
    PUT accesspoints
    {
      "SDCERR": 0,
      "InfoMsg": "Scan requested"
    }

    # ./accesspoints_get.sh

    =========================
    Get accesspoints
    {
      "SDCERR": 0,
      "InfoMsg": "",
      "accesspoints": [
        {
          "SSID": "BillWiTheScienceFi",
          "HwAddress": "6A:D7:9A:14:AE:8E",
          "Strength": 43,
          "MaxBitrate": 540000,
          "Frequency": 5240,
          "Flags": 1,
          "WpaFlags": 0,
          "RsnFlags": 392,
          "LastSeen": 9420,
          "Security": "WPA2 PSK",
          "Keymgmt": "wpa-psk"
        },
        {
          "SSID": "The Promised LAN",
          "HwAddress": "6A:D7:9A:34:AE:8E",
          "Strength": 39,
          "MaxBitrate": 540000,
          "Frequency": 5240,
          "Flags": 1,
          "WpaFlags": 0,
          "RsnFlags": 392,
          "LastSeen": 9399,
          "Security": "WPA2 PSK",
          "Keymgmt": "wpa-psk"
        },
        {
          "SSID": "Accio Internet",
          "HwAddress": "6A:D7:9A:44:AE:8E",
          "Strength": 39,
          "MaxBitrate": 540000,
          "Frequency": 5240,
          "Flags": 1,
          "WpaFlags": 0,
          "RsnFlags": 392,
          "LastSeen": 9399,
          "Security": "WPA2 PSK",
          "Keymgmt": "wpa-psk"
        },
        {
          "SSID": "",
          "HwAddress": "68:D7:9A:24:AE:8E",
          "Strength": 39,
          "MaxBitrate": 540000,
          "Frequency": 5240,
          "Flags": 1,
          "WpaFlags": 0,
          "RsnFlags": 392,
          "LastSeen": 9399,
          "Security": "WPA2 PSK",
          "Keymgmt": "wpa-psk"
        },
        {
          "SSID": "Answer me these questions three",
          "HwAddress": "6A:D7:9A:24:AE:8E",
          "Strength": 39,
          "MaxBitrate": 540000,
          "Frequency": 5240,
          "Flags": 1,
          "WpaFlags": 0,
          "RsnFlags": 392,
          "LastSeen": 9399,
          "Security": "WPA2 PSK",
          "Keymgmt": "wpa-psk"
        },
        {
          "SSID": "psk",
          "HwAddress": "08:D0:9F:C2:ED:E0",
          "Strength": 35,
          "MaxBitrate": 270000,
          "Frequency": 5200,
          "Flags": 1,
          "WpaFlags": 0,
          "RsnFlags": 392,
          "LastSeen": 9390,
          "Security": "WPA2 PSK",
          "Keymgmt": "wpa-psk"
        },
        {
          "SSID": "",
          "HwAddress": "68:D7:9A:24:AE:8D",
          "Strength": 17,
          "MaxBitrate": 130000,
          "Frequency": 2437,
          "Flags": 1,
          "WpaFlags": 0,
          "RsnFlags": 392,
          "LastSeen": 9346,
          "Security": "WPA2 PSK",
          "Keymgmt": "wpa-psk"
        },
        {
          "SSID": "The Promised LAN",
          "HwAddress": "6A:D7:9A:34:AE:8D",
          "Strength": 15,
          "MaxBitrate": 130000,
          "Frequency": 2437,
          "Flags": 1,
          "WpaFlags": 0,
          "RsnFlags": 392,
          "LastSeen": 9387,
          "Security": "WPA2 PSK",
          "Keymgmt": "wpa-psk"
        },
        {
          "SSID": "Answer me these questions three",
          "HwAddress": "6A:D7:9A:24:AE:8D",
          "Strength": 15,
          "MaxBitrate": 130000,
          "Frequency": 2437,
          "Flags": 1,
          "WpaFlags": 0,
          "RsnFlags": 392,
          "LastSeen": 9387,
          "Security": "WPA2 PSK",
          "Keymgmt": "wpa-psk"
        },
        {
          "SSID": "Accio Internet",
          "HwAddress": "6A:D7:9A:44:AE:8D",
          "Strength": 17,
          "MaxBitrate": 130000,
          "Frequency": 2437,
          "Flags": 1,
          "WpaFlags": 0,
          "RsnFlags": 392,
          "LastSeen": 9387,
          "Security": "WPA2 PSK",
          "Keymgmt": "wpa-psk"
        },
        {
          "SSID": "open",
          "HwAddress": "08:D0:9F:BF:74:F0",
          "Strength": 30,
          "MaxBitrate": 130000,
          "Frequency": 2412,
          "Flags": 0,
          "WpaFlags": 0,
          "RsnFlags": 0,
          "LastSeen": 9344,
          "Security": "",
          "Keymgmt": "none"
        }
      ]
    }

# log data query

    # ./logSetting_post.sh

    =========================
    Set LogLevel
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    #./logData_get.sh

    =========================
    Get LogData
    {
      "SDCERR": 0,
      "InfoMsg": "type: JournalctlLogTypesEnum.ALL; days: -1; Priority: 6",
      "count": 473,
      "log": [
        {
          "time": "2024-09-17 23:49:08.383754",
          "priority": "6",
          "identifier": "kernel",
          "message": "Booting Linux on physical CPU 0x0"
        },
        {
          "time": "2024-09-17 23:49:08.384704",
          "priority": "5",
          "identifier": "kernel",
          "message": "Linux version 4.19.203 (buildroot@buildroot) () #1 PREEMPT none"
        },
        {
          "time": "2024-09-17 23:49:08.395830",
          "priority": "6",
          "identifier": "kernel",
          "message": "CPU: ARMv7 Processor [410fc051] revision 1 (ARMv7), cr=10c53c7d"
        },
        {
          "time": "2024-09-17 23:49:08.416038",
          "priority": "6",
          "identifier": "kernel",
          "message": "CPU: PIPT / VIPT nonaliasing data cache, VIPT aliasing instruction cache"
        }
      ]
    }
    <data truncated>


# user management
## By default, no users can be added.  The settings.ini file requires an entry to allow addional users other than root

    # ./users_post.sh

    =========================
    Add user
    {"SDCERR": 1, "InfoMsg": "Max number of users reached"}

### using sshpass here.  You may need to initiate an ssh session prior to using sshpass in order to be prompted to save ssh fingerprint

    sshpass -p summit ssh root@192.168.1.233 "echo -e '\n[settings]\nmax_web_clients=5\n' >>  /data/secret/summit-rcm/summit-rcm-settings.ini"

    # ./users_post.sh

    =========================
    Add user
    {
      "SDCERR": 0,
      "InfoMsg": "User added"
    }


    # ./users_post.sh

    =========================
    Add user
    {
      "SDCERR": 1,
      "InfoMsg": "user test already exists"
    }


    # ./users_delete.sh

    =========================
    del user
    {
      "SDCERR": 0,
      "InfoMsg": "User deleted"
    }


    # ./users_delete.sh

    =========================
    del user
    {
      "SDCERR": 1,
      "InfoMsg": "user test not found"
    }

## for change password, see login/logout section at beginning of this document

# Date and Time

     ./datetime_get.sh

    =========================
    Get datetime
    {
      "zones": [
        "Africa/Abidjan",
        "Africa/Algiers",
        "Africa/Bissau",
        "Africa/Cairo",
        "Africa/Casablanca",
        "Africa/Ceuta",
        "Africa/El_Aaiun",
        "Africa/Johannesburg",
        "Africa/Juba",
        "Africa/Khartoum",
        "Africa/Lagos",
        "Africa/Maputo",
        "Africa/Monrovia",
        "Africa/Nairobi",
        "Africa/Ndjamena",
        "Africa/Sao_Tome",
        "Africa/Tripoli",
        "Africa/Tunis",
        "Africa/Windhoek",
        "America/Adak",
        "America/Anchorage",
        "America/Araguaina",
        "America/Argentina/Buenos_Aires",
        "America/Argentina/Catamarca",
        "America/Argentina/Cordoba",
        "America/Argentina/Jujuy",
        "America/Argentina/La_Rioja",
        "America/Argentina/Mendoza",
        "America/Argentina/Rio_Gallegos",
        "America/Argentina/Salta",
        "America/Argentina/San_Juan",
        "America/Argentina/San_Luis",
        "America/Argentina/Tucuman",
        "America/Argentina/Ushuaia",
        "America/Asuncion",
        "America/Bahia",
        "America/Bahia_Banderas",
        "America/Barbados",
        "America/Belem",
        "America/Belize",
        "America/Boa_Vista",
        "America/Bogota",
        "America/Boise",
        "America/Cambridge_Bay",
        "America/Campo_Grande",
        "America/Cancun",
        "America/Caracas",
        "America/Cayenne",
        "America/Chicago",
        "America/Chihuahua",
        "America/Ciudad_Juarez",
        "America/Costa_Rica",
        "America/Cuiaba",
        "America/Danmarkshavn",
        "America/Dawson",
        "America/Dawson_Creek",
        "America/Denver",
        "America/Detroit",
        "America/Edmonton",
        "America/Eirunepe",
        "America/El_Salvador",
        "America/Fort_Nelson",
        "America/Fortaleza",
        "America/Glace_Bay",
        "America/Goose_Bay",
        "America/Grand_Turk",
        "America/Guatemala",
        "America/Guayaquil",
        "America/Guyana",
        "America/Halifax",
        "America/Havana",
        "America/Hermosillo",
        "America/Indiana/Indianapolis",
        "America/Indiana/Knox",
        "America/Indiana/Marengo",
        "America/Indiana/Petersburg",
        "America/Indiana/Tell_City",
        "America/Indiana/Vevay",
        "America/Indiana/Vincennes",
        "America/Indiana/Winamac",
        "America/Inuvik",
        "America/Iqaluit",
        "America/Jamaica",
        "America/Juneau",
        "America/Kentucky/Louisville",
        "America/Kentucky/Monticello",
        "America/La_Paz",
        "America/Lima",
        "America/Los_Angeles",
        "America/Maceio",
        "America/Managua",
        "America/Manaus",
        "America/Martinique",
        "America/Matamoros",
        "America/Mazatlan",
        "America/Menominee",
        "America/Merida",
        "America/Metlakatla",
        "America/Mexico_City",
        "America/Miquelon",
        "America/Moncton",
        "America/Monterrey",
        "America/Montevideo",
        "America/New_York",
        "America/Nome",
        "America/Noronha",
        "America/North_Dakota/Beulah",
        "America/North_Dakota/Center",
        "America/North_Dakota/New_Salem",
        "America/Nuuk",
        "America/Ojinaga",
        "America/Panama",
        "America/Paramaribo",
        "America/Phoenix",
        "America/Port-au-Prince",
        "America/Porto_Velho",
        "America/Puerto_Rico",
        "America/Punta_Arenas",
        "America/Rankin_Inlet",
        "America/Recife",
        "America/Regina",
        "America/Resolute",
        "America/Rio_Branco",
        "America/Santarem",
        "America/Santiago",
        "America/Santo_Domingo",
        "America/Sao_Paulo",
        "America/Scoresbysund",
        "America/Sitka",
        "America/St_Johns",
        "America/Swift_Current",
        "America/Tegucigalpa",
        "America/Thule",
        "America/Tijuana",
        "America/Toronto",
        "America/Vancouver",
        "America/Whitehorse",
        "America/Winnipeg",
        "America/Yakutat",
        "Antarctica/Casey",
        "Antarctica/Davis",
        "Antarctica/Macquarie",
        "Antarctica/Mawson",
        "Antarctica/Palmer",
        "Antarctica/Rothera",
        "Antarctica/Troll",
        "Antarctica/Vostok",
        "Asia/Almaty",
        "Asia/Amman",
        "Asia/Anadyr",
        "Asia/Aqtau",
        "Asia/Aqtobe",
        "Asia/Ashgabat",
        "Asia/Atyrau",
        "Asia/Baghdad",
        "Asia/Baku",
        "Asia/Bangkok",
        "Asia/Barnaul",
        "Asia/Beirut",
        "Asia/Bishkek",
        "Asia/Chita",
        "Asia/Colombo",
        "Asia/Damascus",
        "Asia/Dhaka",
        "Asia/Dili",
        "Asia/Dubai",
        "Asia/Dushanbe",
        "Asia/Famagusta",
        "Asia/Gaza",
        "Asia/Hebron",
        "Asia/Ho_Chi_Minh",
        "Asia/Hong_Kong",
        "Asia/Hovd",
        "Asia/Irkutsk",
        "Asia/Jakarta",
        "Asia/Jayapura",
        "Asia/Jerusalem",
        "Asia/Kabul",
        "Asia/Kamchatka",
        "Asia/Karachi",
        "Asia/Kathmandu",
        "Asia/Khandyga",
        "Asia/Kolkata",
        "Asia/Krasnoyarsk",
        "Asia/Kuching",
        "Asia/Macau",
        "Asia/Magadan",
        "Asia/Makassar",
        "Asia/Manila",
        "Asia/Nicosia",
        "Asia/Novokuznetsk",
        "Asia/Novosibirsk",
        "Asia/Omsk",
        "Asia/Oral",
        "Asia/Pontianak",
        "Asia/Pyongyang",
        "Asia/Qatar",
        "Asia/Qostanay",
        "Asia/Qyzylorda",
        "Asia/Riyadh",
        "Asia/Sakhalin",
        "Asia/Samarkand",
        "Asia/Seoul",
        "Asia/Shanghai",
        "Asia/Singapore",
        "Asia/Srednekolymsk",
        "Asia/Taipei",
        "Asia/Tashkent",
        "Asia/Tbilisi",
        "Asia/Tehran",
        "Asia/Thimphu",
        "Asia/Tokyo",
        "Asia/Tomsk",
        "Asia/Ulaanbaatar",
        "Asia/Urumqi",
        "Asia/Ust-Nera",
        "Asia/Vladivostok",
        "Asia/Yakutsk",
        "Asia/Yangon",
        "Asia/Yekaterinburg",
        "Asia/Yerevan",
        "Atlantic/Azores",
        "Atlantic/Bermuda",
        "Atlantic/Canary",
        "Atlantic/Cape_Verde",
        "Atlantic/Faroe",
        "Atlantic/Madeira",
        "Atlantic/South_Georgia",
        "Atlantic/Stanley",
        "Australia/Adelaide",
        "Australia/Brisbane",
        "Australia/Broken_Hill",
        "Australia/Darwin",
        "Australia/Eucla",
        "Australia/Hobart",
        "Australia/Lindeman",
        "Australia/Lord_Howe",
        "Australia/Melbourne",
        "Australia/Perth",
        "Australia/Sydney",
        "Europe/Andorra",
        "Europe/Astrakhan",
        "Europe/Athens",
        "Europe/Belgrade",
        "Europe/Berlin",
        "Europe/Brussels",
        "Europe/Bucharest",
        "Europe/Budapest",
        "Europe/Chisinau",
        "Europe/Dublin",
        "Europe/Gibraltar",
        "Europe/Helsinki",
        "Europe/Istanbul",
        "Europe/Kaliningrad",
        "Europe/Kirov",
        "Europe/Kyiv",
        "Europe/Lisbon",
        "Europe/London",
        "Europe/Madrid",
        "Europe/Malta",
        "Europe/Minsk",
        "Europe/Moscow",
        "Europe/Paris",
        "Europe/Prague",
        "Europe/Riga",
        "Europe/Rome",
        "Europe/Samara",
        "Europe/Saratov",
        "Europe/Simferopol",
        "Europe/Sofia",
        "Europe/Tallinn",
        "Europe/Tirane",
        "Europe/Ulyanovsk",
        "Europe/Vienna",
        "Europe/Vilnius",
        "Europe/Volgograd",
        "Europe/Warsaw",
        "Europe/Zurich",
        "Indian/Chagos",
        "Indian/Maldives",
        "Indian/Mauritius",
        "Pacific/Apia",
        "Pacific/Auckland",
        "Pacific/Bougainville",
        "Pacific/Chatham",
        "Pacific/Easter",
        "Pacific/Efate",
        "Pacific/Fakaofo",
        "Pacific/Fiji",
        "Pacific/Galapagos",
        "Pacific/Gambier",
        "Pacific/Guadalcanal",
        "Pacific/Guam",
        "Pacific/Honolulu",
        "Pacific/Kanton",
        "Pacific/Kiritimati",
        "Pacific/Kosrae",
        "Pacific/Kwajalein",
        "Pacific/Marquesas",
        "Pacific/Nauru",
        "Pacific/Niue",
        "Pacific/Norfolk",
        "Pacific/Noumea",
        "Pacific/Pago_Pago",
        "Pacific/Palau",
        "Pacific/Pitcairn",
        "Pacific/Port_Moresby",
        "Pacific/Rarotonga",
        "Pacific/Tahiti",
        "Pacific/Tarawa",
        "Pacific/Tongatapu",
        "UTC"
      ],
      "zone": "America/New_York",
      "method": "auto",
      "time": "2021-10-11 15:51:55",
      "SDCERR": 0,
      "InfoMsg": ""
    }


    # ./datetime_put_datetime.sh

    =========================
    Set datetime
    {
      "time": "2021-10-11 15:52:02",
      "SDCERR": 0,
      "InfoMsg": ""
    }

### ./datetime_put.sh will change the timezone

    # TZ='America/New_York' ./datetime_put.sh

    =========================
    Set time zone
    {
      "time": "2021-10-11 15:52:07",
      "SDCERR": 0,
      "InfoMsg": "America/New_York"
    }

# Factory reset / reboot

    # ./factoryReset_put.sh

    =========================
    Factory Reset
    {
      "SDCERR": 0,
      "InfoMsg": "Reboot required"
    }


    =========================
    Reboot required


    # ./reboot_put.sh

    =========================
    Factory Reset


    =========================
    Reboot
    {
      "SDCERR": 0,
      "InfoMsg": "Reboot initiated"
    }

# download upload encrypted file
## this feature lets you download a config or log encrypted with a supplied password, or a debug file with both encrypted with the sever certificate - appropriate for email

    # ./file_get-config.sh

    =========================
    Get config
    config.zip downloaded

    # ./file_get-log.sh

    =========================
    Get config

    log.zip downloaded.
    # ./file_get-debug.sh

    =========================
    Get config

    debug.encrypt file downloaded. To decrypt:
    openssl cms -decrypt -in debug.encrypt -recip server.crt -inkey server.key -out debug.zip -inform DER

## upload a config.zip configuration:
    # ./file_post-config.sh

    =========================
    POST config

    config.zip uploaded. Reboot to take effect

## delete file
    # FILE=user1.pem TYPE=cert ./file_delete-cert.sh 

    =========================
    Delete cert file for Network Manager
    {"SDCERR": 0, "InfoMsg": "file user1.pem deleted"}

# firmware update

    # ./firmware_update.sh


# version info

    # ./version_get.sh

    =========================
    Versions
    {
      "build": "Summit Linux development build 0.12.0.0",
      "supplicant": "12.0.0.113-40.3.25.3",
      "driver": "lrdmwl_sdio",
      "bluez": "5.72",
      "u-boot": "2024.04-12.0.0.138-som60sd",
      "nm_version": "12.0.0.113-1.46.2",
      "summit_rcm": "12.0.0.153",
      "radio_stack": "12.0.0.113",
      "kernel_vermagic": "4.19.203",
      "current_side": "a",
      "next_side": "a",
      "base_hw_part_number": "453-00004",
      "SDCERR": 0,
      "InfoMsg": ""
    }

#WIFI Geolocation Scanning control (only setable with LITE mode)

    ./awm_get.sh

    =========================
    AWM Get
    {
      "SDCERR": 0,
      "InfoMsg": "AWM configuration only supported in LITE mode",
      "geolocation_scanning_enable": 1
    }

    # ./awm_put.sh

    =========================
    AWM PUT
    empty:

    {
      "SDCERR": 1,
      "InfoMsg": "AWM's geolocation scanning configuration only supported in LITE mode",
      "geolocation_scanning_enable": 1
    }



    set:

    {
      "SDCERR": 1,
      "InfoMsg": "AWM's geolocation scanning configuration only supported in LITE mode",
      "geolocation_scanning_enable": 1
    }



    unset:

    {
      "SDCERR": 1,
      "InfoMsg": "AWM's geolocation scanning configuration only supported in LITE mode",
      "geolocation_scanning_enable": 1
    }

# Fips

    # ./fips_get.sh

    =========================
    Fips Get
    {
      "SDCERR": 0,
      "InfoMsg": "Not a FIPS image",
      "status": "unset"
    }

    # ./fips_put.sh

    =========================
    Fips GET
    {
      "SDCERR": 0,
      "InfoMsg": "Not a FIPS image",
      "status": "unset"
    }

    =========================
    Fips PUT
    empty:

    {
      "SDCERR": 1,
      "InfoMsg": "Invalid option: no option provided"
    }


    invalid:

    {
      "SDCERR": 1,
      "InfoMsg": "Invalid option: status"
    }


    unset:

    {
      "SDCERR": 1,
      "InfoMsg": "Not a FIPS image"
    }

    Change in FIPS state not active until system reboot


# bluetooth

    # ./bluetooth_scan.sh

    =========================
    Bluetooth scan
    reset controller, clear cache and force fresh scan:

    {
      "SDCERR": 0,
      "InfoMsg": ""
    }



    scan:

    {
      "SDCERR": 0,
      "InfoMsg": ""
    }



    confirm:

    {
      "SDCERR": 0,
      "InfoMsg": "",
      "controller0": {
        "discovering": 1,
        "powered": 1,
        "discoverable": 1
      }
    }

    results:

    {
      "SDCERR": 0,
      "InfoMsg": "",
      "controller0": {
        "bluetoothDevices": [
          {
            "Address": "C0:EE:40:43:B1:A7",
            "AddressType": "public",
            "Name": "DVK SOM60x2 (43:B1:A4)",
            "Alias": "DVK SOM60x2 (43:B1:A4)",
            "Paired": 1,
            "Trusted": 1,
            "Blocked": 0,
            "LegacyPairing": 0,
            "Connected": 0,
            "UUIDs": [
              "00001800-0000-1000-8000-00805f9b34fb",
              "00001801-0000-1000-8000-00805f9b34fb",
              "0000180a-0000-1000-8000-00805f9b34fb",
              "be98076e-8e8d-11e8-9eb6-529269fb1459"
            ],
            "Modalias": "usb:v1D6Bp0246d0537",
            "Adapter": "/org/bluez/hci0",
            "ServicesResolved": 0
          },
          {
            "Address": "E0:13:7D:9D:2E:45",
            "AddressType": "random",
            "Name": "Nordic_UART_Service",
            "Alias": "Nordic_UART_Service",
            "Appearance": 833,
            "Paired": 0,
            "Trusted": 0,
            "Blocked": 0,
            "LegacyPairing": 0,
            "RSSI": -58,
            "Connected": 0,
            "UUIDs": [
              "00001800-0000-1000-8000-00805f9b34fb",
              "00001801-0000-1000-8000-00805f9b34fb",
              "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
            ],
            "Adapter": "/org/bluez/hci0",
            "ServicesResolved": 0
          }
        ]
      }
    }

    # BT_DEVICE=E0:13:7D:9D:2E:45 ./bluetooth_pair.sh

    =========================
    Bluetooth pair

    enable discovery:

    {
      "SDCERR": 0,
      "InfoMsg": ""
    }



    pair:

    {
      "SDCERR": 0,
      "InfoMsg": ""
    }



    read state:

    {
      "SDCERR": 0,
      "InfoMsg": "",
      "Address": "E0:13:7D:9D:2E:45",
      "AddressType": "random",
      "Name": "Nordic_UART_Service",
      "Alias": "Nordic_UART_Service",
      "Appearance": 833,
      "Paired": 1,
      "Trusted": 0,
      "Blocked": 0,
      "LegacyPairing": 0,
      "RSSI": -58,
      "Connected": 0,
      "UUIDs": [
        "00001800-0000-1000-8000-00805f9b34fb",
        "00001801-0000-1000-8000-00805f9b34fb",
        "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
      ],
      "Adapter": "/org/bluez/hci0",
      "ServicesResolved": 0
    }

    # BT_DEVICE=E0:13:7D:9D:2E:45  ./bluetooth_vsp_connect.sh

    =========================
    Bluetooth virtual serial port (gatt characteristics) connect

    Bluetooth connect:

    {
      "SDCERR": 0
      "InfoMsg": ""
    }


    read Bluetooth state:

    {
      "SDCERR": 0,
      "InfoMsg": "",
      "Address": "E0:13:7D:9D:2E:45",
      "AddressType": "random",
      "Name": "Nordic_UART_Service",
      "Alias": "Nordic_UART_Service",
      "Appearance": 833,
      "Paired": 0,
      "Trusted": 0,
      "Blocked": 0,
      "LegacyPairing": 0,
      "**Connected**": 1,
      "UUIDs": [
        "00001800-0000-1000-8000-00805f9b34fb",
        "00001801-0000-1000-8000-00805f9b34fb",
        "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
      ],
      "Adapter": "/org/bluez/hci0",
      "ServicesResolved": 0
    }


    Short delay to allow VSP service to discover...

    read Bluetooth state:

    {
      "SDCERR": 0,
      "InfoMsg": "",
      "Address": "E0:13:7D:9D:2E:45",
      "AddressType": "random",
      "Name": "Nordic_UART_Service",
      "Alias": "Nordic_UART_Service",
      "Appearance": 833,
      "Paired": 0,
      "Trusted": 0,
      "Blocked": 0,
      "LegacyPairing": 0,
      "Connected": 1,
      "UUIDs": [
        "00001800-0000-1000-8000-00805f9b34fb",
        "00001801-0000-1000-8000-00805f9b34fb",
        "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
      ],
      "Adapter": "/org/bluez/hci0",
      "**ServicesResolved**": 1
    }


    open vsp port 1001:

    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    check VSP service ports:

    {
      "SDCERR": 0,
      "InfoMsg": "",
      "GattConnections": [
        {
          "device": "E0:13:7D:9D:2E:45",
          "port": 1001
        }
      ]
    }


    send data to port:

    {"Received": "0x446174612066726f6d2072656d6f74652e0d"}
    {"Connected": 0}
    {"Error": "Transmit failed", "Data": "0x7465737420646174610a"}



    # BT_DEVICE=E0:13:7D:9D:2E:45  ./bluetooth_vsp_disconnect.sh

    =========================
    Bluetooth virtual serial port (gatt characteristics) disconnect

    close vsp service port:

    {
      "SDCERR": 0,
      "InfoMsg": ""
    }

    check VSP service ports:

    {
      "SDCERR": 0,
      "InfoMsg": "",
      "GattConnections": []
    }

    Bluetooth disconnect:

    {
      "SDCERR": 0
      "InfoMsg": ""
    }


    read Bluetooth state:

    {
      "SDCERR": 0,
      "InfoMsg": "",
      "Address": "E0:13:7D:9D:2E:45",
      "AddressType": "random",
      "Name": "Nordic_UART_Service",
      "Alias": "Nordic_UART_Service",
      "Appearance": 833,
      "Paired": 0,
      "Trusted": 0,
      "Blocked": 0,
      "LegacyPairing": 0,
      "**Connected**": 0,
      "UUIDs": [
        "00001800-0000-1000-8000-00805f9b34fb",
        "00001801-0000-1000-8000-00805f9b34fb",
        "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
      ],
      "Adapter": "/org/bluez/hci0",
      "ServicesResolved": 0
    }

    # BT_DEVICE=00:07:BE:33:80:AB  ./bluetooth_hid_connect.sh

    =========================
    Bluetooth hid barcode scanner connect

    Bluetooth connect:

    {
      "SDCERR": 0
      "InfoMsg": ""
    }


    read Bluetooth state:

    {
      "SDCERR": 0,
      "InfoMsg": "",
      "Address": "00:07:BE:33:80:AB",
      "AddressType": "random",
      "Name": "Datalogic Gryphon GBT4500",
      "Alias": "Datalogic Gryphon GBT4500",
      "Appearance": 962,
      "Icon": "input-keyboard",
      "Paired": 1,
      "Trusted": 0,
      "Blocked": 0,
      "LegacyPairing": 0,
      "RSSI": -67,
      "**Connected**": 1,
      "UUIDs": [
      ],
      "Modalias": "usb:v1915pEEEEd0001",
      "Adapter": "/org/bluez/hci0",
      "ServicesResolved": 1,
      "WakeAllowed": 1
    }


    Short delay to allow HID service to discover and open...


    open vsp port 1001:

    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    check HID service ports:

    {
      "SDCERR": 0,
      "InfoMsg": "00:07:BE:33:80:AB",
      "HidConnections": [
        {
          "device": "",
          "port": 1001
        }
      ]
    }


    connecting to TCP port - please scan a barcode and confirm result:
    {"Received": {"Barcode": "ABCDEF"}}
    {"Received": {"Barcode": "Code 128"}}
    {"Connected": 0}


    # BT_DEVICE=00:07:BE:33:80:AB  ./bluetooth_hid_disconnect.sh

    =========================
    Bluetooth hid barcode scanner disconnect

    close HID service TCP port:

    {
      "SDCERR": 0,
      "InfoMsg": ""
    }

    check HID service ports:

    {
      "SDCERR": 0,
      "InfoMsg": "",
      "HidConnections": []
    }

    Bluetooth disconnect:

    {
      "SDCERR": 0
      "InfoMsg": ""
    }


    read Bluetooth state:

    {
      "SDCERR": 0,
      "InfoMsg": "",
      "Address": "00:07:BE:33:80:AB",
      "AddressType": "random",
      "Name": "Datalogic Gryphon GBT4500",
      "Alias": "Datalogic Gryphon GBT4500",
      "Appearance": 962,
      "Icon": "input-keyboard",
      "Paired": 1,
      "Trusted": 0,
      "Blocked": 0,
      "LegacyPairing": 0,
      "RSSI": -68,
      "**Connected**": 0,
      "UUIDs": [
      ],
      "Modalias": "usb:v1915pEEEEd0001",
      "Adapter": "/org/bluez/hci0",
      "ServicesResolved": 1,
      "WakeAllowed": 1
    }


    # IPADDR=localhost ./bluetooth_ble_start_server.sh
    =========================
    Bluetooth ble server start

    open ble server port 1001:
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }

    listen on port:
    {
        "connect":{
	    "address":"E0:13:7D:9D:2E:45",
	    "connected":true,
	    "services":{
	        "00001801-0000-1000-8000-00805f9b34fb":{
	            "characteristics":[
	                {
	                    "00002b2a-0000-1000-8000-00805f9b34fb":{
	                        "Flags":[
	                            "read"
	                        ]
	                    }
	                },
	                {
	                    "00002b29-0000-1000-8000-00805f9b34fb":{
	                        "Flags":[
	                            "read",
	                            "write"
	                        ]
	                    }
	                },
	                {
	                    "00002a05-0000-1000-8000-00805f9b34fb":{
	                        "Flags":[
	                            "indicate"
	                        ]
	                    }
	                }
	            ]
	        },
	        "6e400001-b5a3-f393-e0a9-e50e24dcca9e":{
	            "characteristics":[
	                {
	                    "6e400002-b5a3-f393-e0a9-e50e24dcca9e":{
	                        "Flags":[
	                            "write-without-response",
	                            "write"
	                        ]
	                    }
	                },
	                {
	                    "6e400003-b5a3-f393-e0a9-e50e24dcca9e":{
	                        "Flags":[
	                            "notify"
	                        ]
	                    }
	                }
	            ]
	        }
	    },
	    "timestamp":1637677328
        }
    }

    {
        "char":{
	    "char_uuid":"6e400003-b5a3-f393-e0a9-e50e24dcca9e",
	    "value":"616f65750d",
	    "service_uuid":"6e400001-b5a3-f393-e0a9-e50e24dcca9e",
	    "address":"E0:13:7D:9D:2E:45",
	    "timestamp":1637677879
        }
    }


    # IPADDR=localhost ./bluetooth_ble_stop_server.sh

    =========================
    Bluetooth ble server stop
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    # IPADDR=localhost ./bluetooth_ble_start_discovery.sh
    =========================
    Bluetooth ble start discovery
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }

    Discovery notification events will be received over the connection previously established by bluetooth_ble_connect, for example:

    Example data received
    {
        "discovery":{
            "Address":"C4:93:D9:2E:C7:B0",
            "Alias":"Erik's Galaxy Note9",
            "Class":5898764,
            "Icon":"phone",
            "Name":"Erik's Galaxy Note9",
            "RSSI":-69,
            "UUIDs":[
                "00001105-0000-1000-8000-00805f9b34fb",
                "0000110a-0000-1000-8000-00805f9b34fb",
                "0000110c-0000-1000-8000-00805f9b34fb",
                "0000110e-0000-1000-8000-00805f9b34fb",
                "00001112-0000-1000-8000-00805f9b34fb",
                "00001115-0000-1000-8000-00805f9b34fb",
                "00001116-0000-1000-8000-00805f9b34fb",
                "0000111f-0000-1000-8000-00805f9b34fb",
                "0000112f-0000-1000-8000-00805f9b34fb",
                "00001200-0000-1000-8000-00805f9b34fb",
                "00001132-0000-1000-8000-00805f9b34fb"
            ],
            "timestamp":1637711953
        }
    }


    # IPADDR=localhost ./bluetooth_ble_stop_discovery.sh
    =========================
    Bluetooth ble stop discovery
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    #IPADDR=localhost BT_DEVICE=E0:13:7D:9D:2E:45  ./bluetooth_ble_connect.sh
    =========================
    Bluetooth ble connect

    Bluetooth connect:

    {
      "SDCERR": 0,
      "InfoMsg": ""
    }

    read Bluetooth state:
    {
      "SDCERR": 0,
      "InfoMsg": "",
      "Address": "E0:13:7D:9D:2E:45",
      "AddressType": "random",
      "Name": "Nordic_UART_Service",
      "Alias": "Nordic_UART_Service",
      "Appearance": 833,
      "Paired": 0,
      "Trusted": 1,
      "Blocked": 0,
      "LegacyPairing": 0,
      "Connected": 1,
      "UUIDs": [
        "00001800-0000-1000-8000-00805f9b34fb",
        "00001801-0000-1000-8000-00805f9b34fb",
        "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
      ],
      "Adapter": "/org/bluez/hci0",
      "ServicesResolved": 0
    }

    Short delay to allow services to discover...
    read Bluetooth state:

    {
      "SDCERR": 0,
      "InfoMsg": "",
      "Address": "E0:13:7D:9D:2E:45",
      "AddressType": "random",
      "Name": "Nordic_UART_Service",
      "Alias": "Nordic_UART_Service",
      "Appearance": 833,
      "Paired": 0,
      "Trusted": 1,
      "Blocked": 0,
      "LegacyPairing": 0,
      "Connected": 1,
      "UUIDs": [
        "00001800-0000-1000-8000-00805f9b34fb",
        "00001801-0000-1000-8000-00805f9b34fb",
        "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
      ],
      "Adapter": "/org/bluez/hci0",
      "ServicesResolved": 1
    }


    # IPADDR=localhost BT_DEVICE=E0:13:7D:9D:2E:45  ./bluetooth_ble_gatt_notify.sh
    =========================
    Bluetooth GATT notify
    Please invoke bluetooth_ble_connect.sh prior to receive response.
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }

    Characteristic notification events will be received over the connection previously established by bluetooth_ble_connect, for example:
    {
        "char":{
            "char_uuid":"6e400003-b5a3-f393-e0a9-e50e24dcca9e",
            "value":"0d",
            "service_uuid":"6e400001-b5a3-f393-e0a9-e50e24dcca9e",
            "address":"E0:13:7D:9D:2E:45",
            "timestamp":1637709735
        }
    }


    Example of read of heart-rate body sensor location (chest) of example-gatt-server.py
    # IPADDR=localhost BT_DEVICE=C0:EE:40:50:17:6B GATT_SVC_UUID=0000180d-0000-1000-8000-00805f9b34fb GATT_CHR_UUID=00002a38-0000-1000-8000-00805f9b34fb  ./bluetooth_ble_gatt_read.sh

    =========================
    Bluetooth GATT read
    Please invoke bluetooth_ble_connect.sh prior to receive response.
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }

    Read notification events will be received over the connection previously established by bluetooth_ble_connect, for example:

    {
        "char":{
            "char_uuid":"00002a38-0000-1000-8000-00805f9b34fb",
            "value":"01",
            "service_uuid":"0000180d-0000-1000-8000-00805f9b34fb",
            "address":"C0:EE:40:50:17:6B",
            "timestamp":1637782343
        }
    }


    # IPADDR=localhost BT_DEVICE=E0:13:7D:9D:2E:45  ./bluetooth_ble_gatt_read.sh
    =========================
    Bluetooth GATT read
    Please invoke bluetooth_ble_connect.sh prior to receive response.
    {
      "SDCERR": 1,
      "InfoMsg": "Failed to read device E0:13:7D:9D:2E:45 characteristic 6e400003-b5a3-f393-e0a9-e50e24dcca9e: org.bluez.Error.NotPermitted: Read not permitted"
    }


    Example of write to "Dummy test characteristic" of example-gatt-server.py
    # IPADDR=localhost BT_DEVICE=C0:EE:40:50:17:6B GATT_SVC_UUID=12345678-1234-5678-1234-56789abcdef0 GATT_CHR_UUID=12345678-1234-5678-1234-56789abcdef1 GATT_DATA=0001020304  ./bluetooth_ble_gatt_write.sh
    =========================
    Bluetooth GATT write
    Please invoke bluetooth_ble_connect.sh prior to receive response.
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    # IPADDR=localhost BT_DEVICE=C0:EE:40:50:17:6B GATT_SVC_UUID=0000180d-0000-1000-8000-00805f9b34fb GATT_CHR_UUID=00002a37-0000-1000-8000-00805f9b34fb  ./bluetooth_ble_gatt_notify.sh
    =========================
    Bluetooth GATT notify
    Please invoke bluetooth_ble_connect.sh prior to receive response.
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }

    Notification events will be received over the connection previously established by bluetooth_ble_connect, for example:
    {
        "char":{
            "char_uuid":"00002a37-0000-1000-8000-00805f9b34fb",
            "value":"067f",
            "service_uuid":"0000180d-0000-1000-8000-00805f9b34fb",
            "address":"C0:EE:40:50:17:6B",
            "timestamp":1637783561
        }
    }


## example showing user login timed-out prior to request:

    ./bluetooth_scan.sh

    =========================
    Bluetooth scan
    reset controller, clear cache and force fresh scan:

    parse error: Invalid numeric literal at line 1, column 10


# Extra notes
## Certificate chain of trust - why are we using --insecure flag?

The restful APIs are all using SSL but the certificate on the device may not be installed on your testing machine, or the device might not be named according to the server certificate on the DUT.  We can still use curl with SSL but without certificate validation with the --insecure flag (as all the exmaples do)

if you do not want to use the --insecure on your curl commands:

Think of how the ca certs work for existing web sites.  There are a bunch of global certificate authorities that issue certificates to companies for their web sites.  There is typically one CA certificate for a particular CA authority. The domain name is in the sub-certificates issued to the companies. The validation of trust goes through the certificate chain to the CA certificates but, the domain name comes from the final sub-certificate.

So, first, take a look at the server.crt on the som60 (DUT) itself: (My DUT is 192.168.1.233)

	ssh root@192.168.1.233 "openssl x509 -in /etc/summit-rcm/ssl/server.crt -text -noout" | grep DNS
	root@192.168.1.233's password:
                DNS:test.summit.com, DNS:*.summit.com

The certificate indicates that test.summit.com is where it is expecting to be found so we can point our device to it with that name by adding that to our /etc/hosts file.

Add test.summit.com to your /etc/hosts file with the address of your DUT:

	# cat /etc/hosts | grep summit
	192.168.1.233 test.summit.com

Next, pull the ca.crt from the DUT and put it in the directory from which you are running curl scripts.

	scp root@192.168.1.233:/etc/summit-rcm/ssl/ca.crt .

Finally, replace --insecure with --cacert ca.crt and use the DNS name insead of IPADDR.  Example:

    IPADDR=test.summit.com ./login.sh

## Override global_setting values

Any value provided with global_settings can be overidden at invocation by suppling the desired value before the calling the script.
For instance, the actual strings curl is sending can be examined by adding CURL_APP=echo to the beginning of any command line invocation.  Similarly, the use of the jq app can be overridden.

    CURL_APP=echo JQ_APP=tee ./login.sh

*Note that these substitutions are not persistent - with the exception of IPADDR which is persistent.*
