<!--
SPDX-License-Identifier: LicenseRef-Ezurio-Clause
Copyright (C) 2024 Ezurio LLC.
-->
This is a set up scripts which can be used for testing/verification and examples of usage for the various restful APIs.

These scripts and testing are verified on Ubuntu 20.04 but the curl commands should work on other platforms.  The global_settings will likely only work on Linux variants without modifications.

The intent is for settings that remain consistent amongst all the scripts can be stored in the global_settings file.  The ip address of the Device Under Test (DUT) can be supplied with the variable IPADDR and this will be stored automatically.  Any other changes to global_settings must be manually modified.

The global_settings in my setup are set for after the initial password change.  Therefore, for the initial login, I will supply the original password as a parameter.

Finally, a word about the cookie file.  The login script will save a cookie file over an existing cookie even if the login fails. This could cause you to lose the session id and get errors when trying other commands, including logging out.  To prevent this, you can make a copy of your cookie file with the appropriate command for your system.  If the issue does occur, you can wait for your session to expire (about 10 minutes), restart the summit-rcm.service from the console login, or reboot the DUT. This condition presents itself with a message like:
```html
    <!DOCTYPE html PUBLIC
    "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8"></meta>
        <title>401 Unauthorized</title>
        <style type="text/css">
        #powered_by {
            margin-top: 20px;
            border-top: 2px solid black;
            font-style: italic;
        }

        #traceback {
            color: red;
        }
        </style>
    </head>
        <body>
            <h2>401 Unauthorized</h2>
            <p>No permission -- see authorization schemes</p>
            <pre id="traceback"></pre>
        <div id="powered_by">
          <span>
            Powered by <a href="http://www.cherrypy.org">CherryPy unknown</a>
          </span>
        </div>
        </body>
    </html>
```

If you have the jq app installed on your system, it will attempt to parse the above and return a parse error.  If you get a parse error, try overriding the use of jq by adding 'JQ_APP=tee' at the beginning of the command:

    # JQ_APP=tee ./login.sh

# Determine the IP address of the DUT *(commands not shown)*

# Login / Logout / change password
Assuming an IPADDR has never been set, when the first attempt to use any script, you will get an error.  Example:

    # SUMMIT_RCM_PASSWORD=summit ./login.sh
    IPADDR variable needs to be set.

Supply the IPADDR and results show successful login with a change password required message:

    # IPADDR=192.168.1.233 SUMMIT_RCM_PASSWORD=summit ./login.sh
    =====
    Login
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   124  100    85  100    39    211     97 --:--:-- --:--:-- --:--:--   308
    {
      "SDCERR": 0,
      "REDIRECT": 1,
      "PERMISSION": "",
      "InfoMsg": "Password change required"
    }

Note that the login is successful (and therefore the cookie is valid) but a password change is required. The current cookie file is used in the change_pw script:

    # ./change_pw.sh

    =====
    Change password
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   144  100    69  100    75    175    190 --:--:-- --:--:-- --:--:--   365
    {
      "SDCERR": 0,
      "REDIRECT": 1,
      "InfoMsg": "password changed"
    }

Logout and login with new password:
    # ./logout.sh

    ======
    logout
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    48  100    48    0     0    121      0 --:--:-- --:--:-- --:--:--   121
    {
      "SDCERR": 0,
      "InfoMsg": "user root logged out"
    }

    # ./login.sh

    =====
    Login
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   387  100   344  100    43   1283    160 --:--:-- --:--:-- --:--:--  1438
    {
      "SDCERR": 0,
      "REDIRECT": 0,
      "PERMISSION": "status_networking networking_connections networking_edit networking_activate networking_ap_activate networking_delete networking_scan networking_certs logging help_version system_datetime system_swupdate system_password system_advanced system_positioning system_reboot ",
      "InfoMsg": "User logged in"
    }

# Network Status

./network_status.sh
=========================
    network status
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   904  100   904    0     0   1494      0 --:--:-- --:--:-- --:--:--  1494
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

    # ./connections.sh
    =========================
    Connections
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   295  100   295    0     0    417      0 --:--:-- --:--:-- --:--:--   417
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

    # for connection in summit-rcm_*; do echo $connection; ./$connection; done
    summit-rcm_EAP-TLS-ca-cert.sh
    EAP TLS CA cert

    =========================
    Create connection
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   999  100    28  100   971     21    728  0:00:01  0:00:01 --:--:--   750
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    summit-rcm_EAP-TLS-no-cert.sh
    EAP TLS w/o CA cert

    =========================
    Create connection
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   965  100    28  100   937     21    729  0:00:01  0:00:01 --:--:--   750
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    summit-rcm_EAP-TTLS-CA-cert.sh
    EAP TLS w/o cert

    =========================
    Create connection
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   960  100    28  100   932     19    637  0:00:01  0:00:01 --:--:--   656
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    summit-rcm_EAP-TTLS-no-cert.sh
    EAP TTLS w/o CA cert

    =========================
    Create connection
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   926  100    28  100   898     14    457  0:00:02  0:00:01  0:00:01   472
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    summit-rcm_PEAP-GTC-CA-cert.sh

    PEAP GTC w/CA cert

    =========================
    Create connection
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   804  100    28  100   776     16    466  0:00:01  0:00:01 --:--:--   482
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    summit-rcm_PEAP-GTC-NO-cert.sh

    PEAP GTC w/o CA cert

    =========================
    Create connection
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   770  100    28  100   742     14    389  0:00:02  0:00:01  0:00:01   404
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    summit-rcm_PEAP-MSCHAPv2-CA-cert.sh

    PEAP MSCHAPv2 w/CA cert

    =========================
    Create connection
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   819  100    28  100   791     14    405  0:00:02  0:00:01  0:00:01   419
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    summit-rcm_PEAP-MSCHAPv2-no-cert.sh

    PEAP MSCHAPv2 w/o CA cert

    =========================
    Create connection
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   785  100    28  100   757     14    381  0:00:02  0:00:01  0:00:01   395
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }

## created connections:

    ./connections.sh
    =========================
    Connections
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   988  100   988    0     0    740      0  0:00:01  0:00:01 --:--:--   741
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

    # for UUID in `JQ_APP=tee ./connections.sh |\
             jq -R 'fromjson? |\
             select(type == "object")'|\
             jq '.connections | [ to_entries[] | {uuid: .key} + .value]'|\
             jq '[ .[] | select(.id|test(".*CERT.*")) ]' |\
             jq '.[].uuid' |
             tr -d \"`;
             do
                 UUID=${UUID} ./connection_get.sh;
             done
     % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   988  100   988    0     0    614      0  0:00:01  0:00:01 --:--:--   614
    a7b534f2-a739-44d7-a8d3-6bb62f5fee65

    =========================
    Get connection
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100  1008  100  1008    0     0    763      0  0:00:01  0:00:01 --:--:--   762
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
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100  1003  100  1003    0     0    662      0  0:00:01  0:00:01 --:--:--   662
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
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100  1035  100  1035    0     0    708      0  0:00:01  0:00:01 --:--:--   708
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
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100  1030  100  1030    0     0    789      0  0:00:01  0:00:01 --:--:--   789
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
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100  1001  100  1001    0     0    652      0  0:00:01  0:00:01 --:--:--   652
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
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   996  100   996    0     0    660      0  0:00:01  0:00:01 --:--:--   660
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
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100  1016  100  1016    0     0    690      0  0:00:01  0:00:01 --:--:--   690
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
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100  1011  100  1011    0     0    777      0  0:00:01  0:00:01 --:--:--   777
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
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    44  100    44    0     0    125      0 --:--:-- --:--:-- --:--:--   125
    {
      "SDCERR": 1,
      "InfoMsg": "no UUID provided"
    }

## delete the new connections we just created
    # for UUID in `JQ_APP=tee ./connections.sh |\
              jq -R 'fromjson? |\
              select(type == "object")'|\
              jq '.connections | [ to_entries[] | {uuid: .key} + .value]'|\
              jq '[ .[] | select(.id|test(".*CERT.*")) ]' |\
              jq '.[].uuid' |\
                  tr -d \"`;
              do
                  UUID=${UUID} ./connection_delete.sh
              done
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   988  100   988    0     0    655      0  0:00:01  0:00:01 --:--:--   655
    a7b534f2-a739-44d7-a8d3-6bb62f5fee65
    =========================
    DELETE Connection a7b534f2-a739-44d7-a8d3-6bb62f5fee65
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    28  100    28    0     0     20      0  0:00:01  0:00:01 --:--:--    20
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    44a2ce9c-12a4-4205-90f2-0025148a82da
    =========================
    DELETE Connection 44a2ce9c-12a4-4205-90f2-0025148a82da
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    28  100    28    0     0     23      0  0:00:01  0:00:01 --:--:--    23
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    43340c99-d518-44a4-8c87-394e4b931fdd
    =========================
    DELETE Connection 43340c99-d518-44a4-8c87-394e4b931fdd
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    28  100    28    0     0     26      0  0:00:01  0:00:01 --:--:--    26
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    dd30b4ef-3870-46cf-b6ef-02e064ec7192
    =========================
    DELETE Connection dd30b4ef-3870-46cf-b6ef-02e064ec7192
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    28  100    28    0     0     31      0 --:--:-- --:--:-- --:--:--    30
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    e39ae926-2dde-455a-9645-953a22e2035a
    =========================
    DELETE Connection e39ae926-2dde-455a-9645-953a22e2035a
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    28  100    28    0     0     35      0 --:--:-- --:--:-- --:--:--    35
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    e4eea0ae-9299-48d5-a879-a1cdb10a1425
    =========================
    DELETE Connection e4eea0ae-9299-48d5-a879-a1cdb10a1425
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    28  100    28    0     0     41      0 --:--:-- --:--:-- --:--:--    41
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    e29e0e05-a7f4-41c0-8d29-aa9a00496de1
    =========================
    DELETE Connection e29e0e05-a7f4-41c0-8d29-aa9a00496de1
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    28  100    28    0     0     47      0 --:--:-- --:--:-- --:--:--    47
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    3bc8bea2-446f-4f03-878d-1426e28540ae
    =========================
    DELETE Connection 3bc8bea2-446f-4f03-878d-1426e28540ae
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    28  100    28    0     0     57      0 --:--:-- --:--:-- --:--:--    57
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }

# networkInterfaces

    # ./networkinterfaces_get.sh

    =========================
    Get networkinterfaces
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    86  100    86    0     0    133      0 --:--:-- --:--:-- --:--:--   133
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

    # ./get_file_list.sh

    =========================
    Get list of pac files
    []

    # FILE=user1.pem ./put_cert_file.sh

    =========================
    Upload cert file for Network Manager

    # TYPE=cert ./get_file_list.sh

    =========================
    Get list of cert files
    ["user1.pem"]

    # FILE=user1.pac ./put_cert_file.sh

    =========================
    Upload cert file for Network Manager


    # ./get_file_list.sh

    =========================
    Get list of pac files
    ["user1.pac"]

# access points

    # ./accesspoints_put.sh

    =========================
    PUT accesspoints
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    48  100    42  100     6     62      8 --:--:-- --:--:-- --:--:--    71
    {
      "SDCERR": 0,
      "InfoMsg": "Scan requested"
    }

    # ./accesspoints_get.sh

    =========================
    Get accesspoints
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100  2523  100  2523    0     0   1014      0  0:00:02  0:00:02 --:--:--  1014
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

    # ./put_loglevel.sh

    =========================
    Set LogLevel
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    77  100    28  100    49     82    144 --:--:-- --:--:-- --:--:--   226
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    #./get_logData.sh

    =========================
    Get LogData
    2021-10-11 19:01:24.928443:#:4:#:NetworkManager:#:<warn>  [1633978884.9281] device (eth0): Activation: failed for connection 'Wired connection 1':#:2021-10-11 19:01:24.941887:#:6:#:NetworkManager:#:<info>  [1633978884.9415] device (eth0): state change: failed -> disconnected (reason 'none', sys-iface-state: 'managed'):#:2021-10-11 19:01:24.974278:#:6:#:NetworkManager:#:<info>  [1633978884.9726] dhcp4 (eth0):
    <data truncated>


# user management
## By default, no users can be added.  The settings.ini file requires an entry to allow addional users other than root

    # ./add_user.sh

    =========================
    Add user
    {"SDCERR": 1, "InfoMsg": "Max number of users reached"}

### using sshpass here.  You may need to initiate an ssh session prior to using sshpass in order to be prompted to save ssh fingerprint

    sshpass -p summit ssh root@192.168.1.233 "echo -e '\n[settings]\nmax_web_clients=5\n' >>  /data/secret/summit-rcm/summit-rcm-settings.ini"

    # ./add_user.sh

    =========================
    Add user
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   366  100    38  100   328     94    813 --:--:-- --:--:-- --:--:--   905
    {
      "SDCERR": 0,
      "InfoMsg": "User added"
    }


    # ./add_user.sh

    =========================
    Add user
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   380  100    52  100   328    231   1457 --:--:-- --:--:-- --:--:--  1688
    {
      "SDCERR": 1,
      "InfoMsg": "user test already exists"
    }


    # ./del_user.sh

    =========================
    del user
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    40  100    40    0     0    174      0 --:--:-- --:--:-- --:--:--   174
    {
      "SDCERR": 0,
      "InfoMsg": "User deleted"
    }


    # ./del_user.sh

    =========================
    del user
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    47  100    47    0     0    268      0 --:--:-- --:--:-- --:--:--   270
    {
      "SDCERR": 1,
      "InfoMsg": "user test not found"
    }

## for change password, see login/logout section at beginning of this document

# Date and Time

     ./get_datetime.sh

    =========================
    Get datetime
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100  8857  100  8857    0     0  30332      0 --:--:-- --:--:-- --:--:-- 30332
    {
      "zones": [
        "Europe/Andorra",
        "Asia/Dubai",
        "Asia/Kabul",
        "America/Antigua",
        "America/Anguilla",
        "Europe/Tirane",
        "Asia/Yerevan",
        "Africa/Luanda",
        "Antarctica/McMurdo",
        "Antarctica/Casey",
        "Antarctica/Davis",
        "Antarctica/DumontDUrville",
        "Antarctica/Mawson",
        "Antarctica/Palmer",
        "Antarctica/Rothera",
        "Antarctica/Syowa",
        "Antarctica/Troll",
        "Antarctica/Vostok",
        "America/Argentina/Buenos_Aires",
        "America/Argentina/Cordoba",
        "America/Argentina/Salta",
        "America/Argentina/Jujuy",
        "America/Argentina/Tucuman",
        "America/Argentina/Catamarca",
        "America/Argentina/La_Rioja",
        "America/Argentina/San_Juan",
        "America/Argentina/Mendoza",
        "America/Argentina/San_Luis",
        "America/Argentina/Rio_Gallegos",
        "America/Argentina/Ushuaia",
        "Pacific/Pago_Pago",
        "Europe/Vienna",
        "Australia/Lord_Howe",
        "Antarctica/Macquarie",
        "Australia/Hobart",
        "Australia/Currie",
        "Australia/Melbourne",
        "Australia/Sydney",
        "Australia/Broken_Hill",
        "Australia/Brisbane",
        "Australia/Lindeman",
        "Australia/Adelaide",
        "Australia/Darwin",
        "Australia/Perth",
        "Australia/Eucla",
        "America/Aruba",
        "Europe/Mariehamn",
        "Asia/Baku",
        "Europe/Sarajevo",
        "America/Barbados",
        "Asia/Dhaka",
        "Europe/Brussels",
        "Africa/Ouagadougou",
        "Europe/Sofia",
        "Asia/Bahrain",
        "Africa/Bujumbura",
        "Africa/Porto-Novo",
        "America/St_Barthelemy",
        "Atlantic/Bermuda",
        "Asia/Brunei",
        "America/La_Paz",
        "America/Kralendijk",
        "America/Noronha",
        "America/Belem",
        "America/Fortaleza",
        "America/Recife",
        "America/Araguaina",
        "America/Maceio",
        "America/Bahia",
        "America/Sao_Paulo",
        "America/Campo_Grande",
        "America/Cuiaba",
        "America/Santarem",
        "America/Porto_Velho",
        "America/Boa_Vista",
        "America/Manaus",
        "America/Eirunepe",
        "America/Rio_Branco",
        "America/Nassau",
        "Asia/Thimphu",
        "Africa/Gaborone",
        "Europe/Minsk",
        "America/Belize",
        "America/St_Johns",
        "America/Halifax",
        "America/Glace_Bay",
        "America/Moncton",
        "America/Goose_Bay",
        "America/Blanc-Sablon",
        "America/Toronto",
        "America/Nipigon",
        "America/Thunder_Bay",
        "America/Iqaluit",
        "America/Pangnirtung",
        "America/Atikokan",
        "America/Winnipeg",
        "America/Rainy_River",
        "America/Resolute",
        "America/Rankin_Inlet",
        "America/Regina",
        "America/Swift_Current",
        "America/Edmonton",
        "America/Cambridge_Bay",
        "America/Yellowknife",
        "America/Inuvik",
        "America/Creston",
        "America/Dawson_Creek",
        "America/Fort_Nelson",
        "America/Vancouver",
        "America/Whitehorse",
        "America/Dawson",
        "Indian/Cocos",
        "Africa/Kinshasa",
        "Africa/Lubumbashi",
        "Africa/Bangui",
        "Africa/Brazzaville",
        "Europe/Zurich",
        "Africa/Abidjan",
        "Pacific/Rarotonga",
        "America/Santiago",
        "America/Punta_Arenas",
        "Pacific/Easter",
        "Africa/Douala",
        "Asia/Shanghai",
        "Asia/Urumqi",
        "America/Bogota",
        "America/Costa_Rica",
        "America/Havana",
        "Atlantic/Cape_Verde",
        "America/Curacao",
        "Indian/Christmas",
        "Asia/Nicosia",
        "Asia/Famagusta",
        "Europe/Prague",
        "Europe/Berlin",
        "Europe/Busingen",
        "Africa/Djibouti",
        "Europe/Copenhagen",
        "America/Dominica",
        "America/Santo_Domingo",
        "Africa/Algiers",
        "America/Guayaquil",
        "Pacific/Galapagos",
        "Europe/Tallinn",
        "Africa/Cairo",
        "Africa/El_Aaiun",
        "Africa/Asmara",
        "Europe/Madrid",
        "Africa/Ceuta",
        "Atlantic/Canary",
        "Africa/Addis_Ababa",
        "Europe/Helsinki",
        "Pacific/Fiji",
        "Atlantic/Stanley",
        "Pacific/Chuuk",
        "Pacific/Pohnpei",
        "Pacific/Kosrae",
        "Atlantic/Faroe",
        "Europe/Paris",
        "Africa/Libreville",
        "Europe/London",
        "America/Grenada",
        "Asia/Tbilisi",
        "America/Cayenne",
        "Europe/Guernsey",
        "Africa/Accra",
        "Europe/Gibraltar",
        "America/Godthab",
        "America/Danmarkshavn",
        "America/Scoresbysund",
        "America/Thule",
        "Africa/Banjul",
        "Africa/Conakry",
        "America/Guadeloupe",
        "Africa/Malabo",
        "Europe/Athens",
        "Atlantic/South_Georgia",
        "America/Guatemala",
        "Pacific/Guam",
        "Africa/Bissau",
        "America/Guyana",
        "Asia/Hong_Kong",
        "America/Tegucigalpa",
        "Europe/Zagreb",
        "America/Port-au-Prince",
        "Europe/Budapest",
        "Asia/Jakarta",
        "Asia/Pontianak",
        "Asia/Makassar",
        "Asia/Jayapura",
        "Europe/Dublin",
        "Asia/Jerusalem",
        "Europe/Isle_of_Man",
        "Asia/Kolkata",
        "Indian/Chagos",
        "Asia/Baghdad",
        "Asia/Tehran",
        "Atlantic/Reykjavik",
        "Europe/Rome",
        "Europe/Jersey",
        "America/Jamaica",
        "Asia/Amman",
        "Asia/Tokyo",
        "Africa/Nairobi",
        "Asia/Bishkek",
        "Asia/Phnom_Penh",
        "Pacific/Tarawa",
        "Pacific/Enderbury",
        "Pacific/Kiritimati",
        "Indian/Comoro",
        "America/St_Kitts",
        "Asia/Pyongyang",
        "Asia/Seoul",
        "Asia/Kuwait",
        "America/Cayman",
        "Asia/Almaty",
        "Asia/Qyzylorda",
        "Asia/Aqtobe",
        "Asia/Aqtau",
        "Asia/Atyrau",
        "Asia/Oral",
        "Asia/Vientiane",
        "Asia/Beirut",
        "America/St_Lucia",
        "Europe/Vaduz",
        "Asia/Colombo",
        "Africa/Monrovia",
        "Africa/Maseru",
        "Europe/Vilnius",
        "Europe/Luxembourg",
        "Europe/Riga",
        "Africa/Tripoli",
        "Africa/Casablanca",
        "Europe/Monaco",
        "Europe/Chisinau",
        "Europe/Podgorica",
        "America/Marigot",
        "Indian/Antananarivo",
        "Pacific/Majuro",
        "Pacific/Kwajalein",
        "Europe/Skopje",
        "Africa/Bamako",
        "Asia/Yangon",
        "Asia/Ulaanbaatar",
        "Asia/Hovd",
        "Asia/Choibalsan",
        "Asia/Macau",
        "Pacific/Saipan",
        "America/Martinique",
        "Africa/Nouakchott",
        "America/Montserrat",
        "Europe/Malta",
        "Indian/Mauritius",
        "Indian/Maldives",
        "Africa/Blantyre",
        "America/Mexico_City",
        "America/Cancun",
        "America/Merida",
        "America/Monterrey",
        "America/Matamoros",
        "America/Mazatlan",
        "America/Chihuahua",
        "America/Ojinaga",
        "America/Hermosillo",
        "America/Tijuana",
        "America/Bahia_Banderas",
        "Asia/Kuala_Lumpur",
        "Asia/Kuching",
        "Africa/Maputo",
        "Africa/Windhoek",
        "Pacific/Noumea",
        "Africa/Niamey",
        "Pacific/Norfolk",
        "Africa/Lagos",
        "America/Managua",
        "Europe/Amsterdam",
        "Europe/Oslo",
        "Asia/Kathmandu",
        "Pacific/Nauru",
        "Pacific/Niue",
        "Pacific/Auckland",
        "Pacific/Chatham",
        "Asia/Muscat",
        "America/Panama",
        "America/Lima",
        "Pacific/Tahiti",
        "Pacific/Marquesas",
        "Pacific/Gambier",
        "Pacific/Port_Moresby",
        "Pacific/Bougainville",
        "Asia/Manila",
        "Asia/Karachi",
        "Europe/Warsaw",
        "America/Miquelon",
        "Pacific/Pitcairn",
        "America/Puerto_Rico",
        "Asia/Gaza",
        "Asia/Hebron",
        "Europe/Lisbon",
        "Atlantic/Madeira",
        "Atlantic/Azores",
        "Pacific/Palau",
        "America/Asuncion",
        "Asia/Qatar",
        "Indian/Reunion",
        "Europe/Bucharest",
        "Europe/Belgrade",
        "Europe/Kaliningrad",
        "Europe/Moscow",
        "Europe/Simferopol",
        "Europe/Volgograd",
        "Europe/Kirov",
        "Europe/Astrakhan",
        "Europe/Saratov",
        "Europe/Ulyanovsk",
        "Europe/Samara",
        "Asia/Yekaterinburg",
        "Asia/Omsk",
        "Asia/Novosibirsk",
        "Asia/Barnaul",
        "Asia/Tomsk",
        "Asia/Novokuznetsk",
        "Asia/Krasnoyarsk",
        "Asia/Irkutsk",
        "Asia/Chita",
        "Asia/Yakutsk",
        "Asia/Khandyga",
        "Asia/Vladivostok",
        "Asia/Ust-Nera",
        "Asia/Magadan",
        "Asia/Sakhalin",
        "Asia/Srednekolymsk",
        "Asia/Kamchatka",
        "Asia/Anadyr",
        "Africa/Kigali",
        "Asia/Riyadh",
        "Pacific/Guadalcanal",
        "Indian/Mahe",
        "Africa/Khartoum",
        "Europe/Stockholm",
        "Asia/Singapore",
        "Atlantic/St_Helena",
        "Europe/Ljubljana",
        "Arctic/Longyearbyen",
        "Europe/Bratislava",
        "Africa/Freetown",
        "Europe/San_Marino",
        "Africa/Dakar",
        "Africa/Mogadishu",
        "America/Paramaribo",
        "Africa/Juba",
        "Africa/Sao_Tome",
        "America/El_Salvador",
        "America/Lower_Princes",
        "Asia/Damascus",
        "Africa/Mbabane",
        "America/Grand_Turk",
        "Africa/Ndjamena",
        "Indian/Kerguelen",
        "Africa/Lome",
        "Asia/Bangkok",
        "Asia/Dushanbe",
        "Pacific/Fakaofo",
        "Asia/Dili",
        "Asia/Ashgabat",
        "Africa/Tunis",
        "Pacific/Tongatapu",
        "Europe/Istanbul",
        "America/Port_of_Spain",
        "Pacific/Funafuti",
        "Asia/Taipei",
        "Africa/Dar_es_Salaam",
        "Europe/Kiev",
        "Europe/Uzhgorod",
        "Europe/Zaporozhye",
        "Africa/Kampala",
        "Pacific/Midway",
        "Pacific/Wake",
        "America/New_York",
        "America/Detroit",
        "America/Kentucky/Louisville",
        "America/Kentucky/Monticello",
        "America/Indiana/Indianapolis",
        "America/Indiana/Vincennes",
        "America/Indiana/Winamac",
        "America/Indiana/Marengo",
        "America/Indiana/Petersburg",
        "America/Indiana/Vevay",
        "America/Chicago",
        "America/Indiana/Tell_City",
        "America/Indiana/Knox",
        "America/Menominee",
        "America/North_Dakota/Center",
        "America/North_Dakota/New_Salem",
        "America/North_Dakota/Beulah",
        "America/Denver",
        "America/Boise",
        "America/Phoenix",
        "America/Los_Angeles",
        "America/Anchorage",
        "America/Juneau",
        "America/Sitka",
        "America/Metlakatla",
        "America/Yakutat",
        "America/Nome",
        "America/Adak",
        "Pacific/Honolulu",
        "America/Montevideo",
        "Asia/Samarkand",
        "Asia/Tashkent",
        "Europe/Vatican",
        "America/St_Vincent",
        "America/Caracas",
        "America/Tortola",
        "America/St_Thomas",
        "Asia/Ho_Chi_Minh",
        "Pacific/Efate",
        "Pacific/Wallis",
        "Pacific/Apia",
        "Asia/Aden",
        "Indian/Mayotte",
        "Africa/Johannesburg",
        "Africa/Lusaka",
        "Africa/Harare",
        "Etc/GMT",
        "Etc/GMT-0",
        "Etc/GMT-1",
        "Etc/GMT-10",
        "Etc/GMT-11",
        "Etc/GMT-12",
        "Etc/GMT-13",
        "Etc/GMT-2",
        "Etc/GMT-3",
        "Etc/GMT-4",
        "Etc/GMT-5",
        "Etc/GMT-6",
        "Etc/GMT-7",
        "Etc/GMT-8",
        "Etc/GMT-9",
        "Etc/Greenwich",
        "Etc/Universal",
        "Etc/Zulu",
        "Etc/GMT0",
        "Etc/GMT+0",
        "Etc/GMT+1",
        "Etc/GMT+10",
        "Etc/GMT+11",
        "Etc/GMT+12",
        "Etc/GMT-14",
        "Etc/GMT+2",
        "Etc/GMT+3",
        "Etc/GMT+4",
        "Etc/GMT+5",
        "Etc/GMT+6",
        "Etc/GMT+7",
        "Etc/GMT+8",
        "Etc/GMT+9",
        "Etc/UCT",
        "Etc/UTC"
      ],
      "zone": "America/New_York",
      "method": "manual",
      "time": "2021-10-11 15:51:55\n",
      "SDCERR": 0,
      "InfoMsg": ""
    }


    # TZ='America/New_York' ./set_timezone.sh

    =========================
    Set datetime
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    99  100    61  100    38     37     23  0:00:01  0:00:01 --:--:--    61
    {
      "time": "2021-10-11 15:52:02\n",
      "SDCERR": 0,
      "InfoMsg": ""
    }

### ./set_timezone.sh with no timezone will just return the current time

    # ./set_timezone.sh

    =========================
    Set datetime
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    83  100    61  100    22    194     70 --:--:-- --:--:-- --:--:--   265
    {
      "time": "2021-10-11 15:52:07\n",
      "SDCERR": 0,
      "InfoMsg": ""
    }

# Factory reset / reboot

    # ./factory_reset.sh

    =========================
    Factory Reset
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    43  100    43    0     0     62      0 --:--:-- --:--:-- --:--:--    62
    {
      "SDCERR": 0,
      "InfoMsg": "Reboot required"
    }


    =========================
    Reboot required


    # ./reboot.sh

    =========================
    Factory Reset


    =========================
    Reboot
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    44  100    44    0     0     73      0 --:--:-- --:--:-- --:--:--    74
    {
      "SDCERR": 0,
      "InfoMsg": "Reboot initiated"
    }

# download upload encrypted file
## this feature lets you download a config or log encrypted with a supplied password, or a debug file with both encrypted with the sever certificate - appropriate for email

    # ./get_config.sh

    =========================
    Get config
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   755  100   755    0     0   3106      0 --:--:-- --:--:-- --:--:--  3106
    config.zip downloaded

    # ./get_log.sh

    =========================
    Get config
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   755  100   755    0     0   2233      0 --:--:-- --:--:-- --:--:--  2233

    log.zip downloaded.
    # ./get_debug.sh

    =========================
    Get config
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   755  100   755    0     0   2046      0 --:--:-- --:--:-- --:--:--  2040

    debug.encrtpt file downloaded. To decrypt:
    openssl smime -decrypt -in debug.encrypt -recip server.crt -inkey server.key -out debug.zip --inform DER

## upload a config.zip configuration:
    # ./post_config.sh

    =========================
    POST config

    config.zip uploaded. Reboot to take effect

## delete file
### not working currently

# firmware update

    # ./firmware_update.sh


# version info

    # ./version.sh

    =========================
    Versions
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   229  100   229    0     0    748      0 --:--:-- --:--:-- --:--:--   748
    {
      "nm_version": "9.0.0.15-1.32.4",
      "summit_rcm": "11.0.0.0",
      "build": "Summit Linux development build 0.7.0.0 20211010",
      "supplicant": "sdcsupp v9.0.0.15-40.3.16.26",
      "driver": "lrdmwl_sdio",
      "driver_version": "4.19.203"
    }

#WIFI Geolocation Scanning control (only setable with LITE mode)

    ./awm_get.sh

    =========================
    AWM Get
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   107  100   107    0     0    378      0 --:--:-- --:--:-- --:--:--   376
    {
      "SDCERR": 0,
      "InfoMsg": "AWM configuration only supported in LITE mode",
      "geolocation_scanning_enable": 1
    }

    # ./awm_put.sh

    =========================
    AWM PUT
    empty:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   132  100   130  100     2    714     10 --:--:-- --:--:-- --:--:--   725
    {
      "SDCERR": 1,
      "InfoMsg": "AWM's geolocation scanning configuration only supported in LITE mode",
      "geolocation_scanning_enable": 1
    }



    set:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   163  100   130  100    33    698    177 --:--:-- --:--:-- --:--:--   871
    {
      "SDCERR": 1,
      "InfoMsg": "AWM's geolocation scanning configuration only supported in LITE mode",
      "geolocation_scanning_enable": 1
    }



    unset:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   163  100   130  100    33    684    173 --:--:-- --:--:-- --:--:--   857
    {
      "SDCERR": 1,
      "InfoMsg": "AWM's geolocation scanning configuration only supported in LITE mode",
      "geolocation_scanning_enable": 1
    }

# Positioning
# Positioning Switch

# Fips

    # ./fips_get.sh

    =========================
    Fips Get
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    63  100    63    0     0    127      0 --:--:-- --:--:-- --:--:--   127
    {
      "SDCERR": 0,
      "InfoMsg": "Not a FIPS image",
      "status": "unset"
    }

    # ./fips_put.sh

    =========================
    Fips GET
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    63  100    63    0     0    176      0 --:--:-- --:--:-- --:--:--   175
    {
      "SDCERR": 0,
      "InfoMsg": "Not a FIPS image",
      "status": "unset"
    }

    =========================
    Fips PUT
    empty:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    64  100    62  100     2    179      5 --:--:-- --:--:-- --:--:--   184
    {
      "SDCERR": 1,
      "InfoMsg": "Invalid option: no option provided"
    }


    invalid:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    67  100    50  100    17    135     46 --:--:-- --:--:-- --:--:--   182
    {
      "SDCERR": 1,
      "InfoMsg": "Invalid option: status"
    }


    unset:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    60  100    44  100    16    107     39 --:--:-- --:--:-- --:--:--   146
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

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    79  100    28  100    51    965   1758 --:--:-- --:--:-- --:--:--  2724
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }



    scan:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    79  100    28  100    51     39     72 --:--:-- --:--:-- --:--:--   111
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }



    confirm:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    96  100    96    0     0   8000      0 --:--:-- --:--:-- --:--:--  8000
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

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100  4449  100  4449    0     0   217k      0 --:--:-- --:--:-- --:--:--  217k
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

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    47  100    28  100    19   2153   1461 --:--:-- --:--:-- --:--:--  3615
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }



    pair:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   104  100    91    0    13      2      0  0:00:45  0:00:31  0:00:14    28
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }



    read state:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   578  100   578    0     0  10703      0 --:--:-- --:--:-- --:--:-- 10703
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

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    29  100    13  100    16     46     57 --:--:-- --:--:-- --:--:--   103
    {
      "SDCERR": 0
      "InfoMsg": ""
    }


    read Bluetooth state:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   428  100   428    0     0  30571      0 --:--:-- --:--:-- --:--:-- 30571
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

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   428  100   428    0     0  30571      0 --:--:-- --:--:-- --:--:-- 30571
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

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   294  100    28  100   266     53    507 --:--:-- --:--:-- --:--:--   561
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    check VSP service ports:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   137  100    96  100    41   7384   3153 --:--:-- --:--:-- --:--:-- 10538
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

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    75  100    28  100    47      7     13  0:00:04  0:00:03  0:00:01    21
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }

    check VSP service ports:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    92  100    51  100    41   3187   2562 --:--:-- --:--:-- --:--:--  5750
    {
      "SDCERR": 0,
      "InfoMsg": "",
      "GattConnections": []
    }

    Bluetooth disconnect:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    29  100    13  100    16    812   1000 --:--:-- --:--:-- --:--:--  1812
    {
      "SDCERR": 0
      "InfoMsg": ""
    }


    read Bluetooth state:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   428  100   428    0     0  28533      0 --:--:-- --:--:-- --:--:-- 28533
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

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    29  100    13  100    16     32     40 --:--:-- --:--:-- --:--:--    72
    {
      "SDCERR": 0
      "InfoMsg": ""
    }


    read Bluetooth state:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   631  100   631    0     0   1719      0 --:--:-- --:--:-- --:--:--  1719
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

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    98  100    28  100    70     51    128 --:--:-- --:--:-- --:--:--   179
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    check HID service ports:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   135  100    95  100    40    281    118 --:--:-- --:--:-- --:--:--   398
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

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    74  100    28  100    46     86    141 --:--:-- --:--:-- --:--:--   228
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }

    check HID service ports:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    90  100    50  100    40    192    153 --:--:-- --:--:-- --:--:--   346
    {
      "SDCERR": 0,
      "InfoMsg": "",
      "HidConnections": []
    }

    Bluetooth disconnect:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    29  100    13  100    16      3      4  0:00:04  0:00:03  0:00:01     8
    {
      "SDCERR": 0
      "InfoMsg": ""
    }


    read Bluetooth state:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   618  100   618    0     0   1889      0 --:--:-- --:--:-- --:--:--  1884
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
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
	                             Dload  Upload   Total   Spent    Left  Speed
    100   102  100    28  100    74      9     24  0:00:03  0:00:03 --:--:--    33
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
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    74  100    28  100    46     15     24  0:00:01  0:00:01 --:--:--    40
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    # IPADDR=localhost ./bluetooth_ble_start_discovery.sh
    =========================
    Bluetooth ble start discovery
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    78  100    28  100    50     52     93 --:--:-- --:--:-- --:--:--   144
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
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    77  100    28  100    49   1217   2130 --:--:-- --:--:-- --:--:--  3347
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    #IPADDR=localhost BT_DEVICE=E0:13:7D:9D:2E:45  ./bluetooth_ble_connect.sh
    =========================
    Bluetooth ble connect

    Bluetooth connect:

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    53  100    28  100    25      8      7  0:00:03  0:00:03 --:--:--    16
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }

    read Bluetooth state:
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   428  100   428    0     0  26750      0 --:--:-- --:--:-- --:--:-- 26750
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

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   428  100   428    0     0  28533      0 --:--:-- --:--:-- --:--:-- 28533
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
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   243  100    28  100   215    358   2756 --:--:-- --:--:-- --:--:--  3115
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
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   215  100    28  100   187    368   2460 --:--:-- --:--:-- --:--:--  2866
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
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   356  100   169  100   187      7      8  0:00:24  0:00:22  0:00:02    46
    {
      "SDCERR": 1,
      "InfoMsg": "Failed to read device E0:13:7D:9D:2E:45 characteristic 6e400003-b5a3-f393-e0a9-e50e24dcca9e: org.bluez.Error.NotPermitted: Read not permitted"
    }


    Example of write to "Dummy test characteristic" of example-gatt-server.py
    # IPADDR=localhost BT_DEVICE=C0:EE:40:50:17:6B GATT_SVC_UUID=12345678-1234-5678-1234-56789abcdef0 GATT_CHR_UUID=12345678-1234-5678-1234-56789abcdef1 GATT_DATA=0001020304  ./bluetooth_ble_gatt_write.sh
    =========================
    Bluetooth GATT write
    Please invoke bluetooth_ble_connect.sh prior to receive response.
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   247  100    28  100   219   1272   9954 --:--:-- --:--:-- --:--:-- 11227
    {
      "SDCERR": 0,
      "InfoMsg": ""
    }


    # IPADDR=localhost BT_DEVICE=C0:EE:40:50:17:6B GATT_SVC_UUID=0000180d-0000-1000-8000-00805f9b34fb GATT_CHR_UUID=00002a37-0000-1000-8000-00805f9b34fb  ./bluetooth_ble_gatt_notify.sh
    =========================
    Bluetooth GATT notify
    Please invoke bluetooth_ble_connect.sh prior to receive response.
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   243  100    28  100   215    337   2590 --:--:-- --:--:-- --:--:--  2927
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

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100   805  100   754  100    51  75400   5100 --:--:-- --:--:-- --:--:-- 80500
    parse error: Invalid numeric literal at line 1, column 10


# Extra notes
## Certificate chain of trust - why are we using --insecure flag?

The restful APIs are all using SSL but the certificate on the device may not be installed on your testing machine, or the device might not be named according to the server certificate on the DUT.  We can still use curl with SSL but without certificate validation with the --insecure flag (as all the exmaples do)

if you do not want to use the --insecure on your curl commands:

Think of how the ca certs work for existing web sites.  There are a bunch of global certificate authorities that issue certificates to companies for their web sites.  There is typically one CA certificate for a paticular CA authority. The domain name is in the sub-certificates issued to the companies. The validation of trust goes through the certificate chain to the CA certificates but, the domain name comes from the final sub-certificate.

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

Any value provided with global_settings can be overidden at invocation buy suppling the desired value before the calling the script.
For instance, the actual strings curl is sending can be examined by adding CURL_APP=echo to the beginning of any command line invocation.  Similarly, the use of the jq app can be overridden.

    CURL_APP=echo JQ_APP=tee ./login.sh

*Note that these substitutions are not persistent - with the exception of IPADDR which is persistent.*

