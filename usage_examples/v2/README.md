<!--
SPDX-License-Identifier: LicenseRef-Ezurio-Clause
Copyright (C) 2025 Ezurio LLC.
-->
# Summit RCM v2 REST API

## Introduction
The RESTful API is designed to return appropriate [HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status) to convey success/failure for a given request. Additionally, most endpoints will accept and return a JSON-formatted message body.

This is a set of scripts which can be used for testing/verification and examples of usage for the various RESTful APIs.

These scripts and testing are verified on Ubuntu 24.04, but the `curl` commands should work on other platforms. The `global_settings` will likely only work on Linux variants without modifications.

The intent is for settings that remain consistent amongst all the scripts are stored in the `global_settings` file. The IP address of the Device Under Test (DUT) can be supplied with the variable `IPADDR`, and this will be stored automatically. Any other changes to `global_settings` must be manually modified.

Finally, a word about the cookie file.  The login script will save a cookie file over an existing cookie even if the login fails. This could cause you to lose the session id and receive errors when trying other commands, including logging out. To prevent this, you can make a copy of your cookie file with the appropriate command for your system. If the issue does occur, you can wait for your session to expire (about 10 minutes), restart the `summit-rcm.service` from the console login, or reboot the DUT. This condition presents itself as a HTTP 401 (Unauthorized) response status code.

NOTE: This is not an issue if the Summit RCM "Allow multiple sessions per user" setting is enabled.

## Login

### Session login
```json
$ SUMMIT_RCM_PASSWORD="summit" ./login_post.sh
=========================
Session login
=========================

Status Code: 200
Response:
```

### Session logout
```json
$ ./login_delete.sh 
=========================
Session logout
=========================

Status Code: 200
Response:
```

### Update user password
```json
$ TARGET_USER_USERNAME="root" CURRENT_PASSWORD="summit" NEW_PASSWORD="newpassword" ./login_users_update_patch.sh 
=========================
Update a current user
=========================

Username: root
Current Password: summit
New Password: newpassword
Permissions: 
Status Code: 200
Response:
{
  "username": "root",
  "permissions": "status_networking networking_connections networking_edit networking_activate networking_ap_activate networking_delete networking_scan networking_certs logging help_version system_datetime system_swupdate system_password system_advanced system_positioning system_reboot system_user"
}
```

## Network

### Status
```json
$ ./network_status_get.sh 
=========================
Get network status
=========================

Status Code: 200
Response:
{
  "status": {
    "lo": {
      "status": {
        "state": 100,
        "stateText": "Activated",
        "mtu": 65536,
        "deviceType": 32,
        "deviceTypeText": "Loopback"
      },
      "activeConnection": {
        "id": "lo",
        "interfaceName": "lo",
        "permissions": [],
        "type": "loopback",
        "uuid": "23f20dd7-4169-4682-af89-a359a7bfbcb4",
        "zone": ""
      },
      "ip4Config": {
        "addressData": [
          {
            "address": "127.0.0.1",
            "prefix": 8
          }
        ],
        "routeData": [],
        "gateway": "",
        "domains": [],
        "nameservers": [],
        "winsServers": []
      },
      "ip6Config": {
        "addressData": [
          {
            "address": "::1",
            "prefix": 128
          }
        ],
        "routeData": [],
        "gateway": "",
        "domains": [],
        "nameservers": []
      },
      "dhcp4Config": {},
      "dhcp6Config": {}
    },
    "eth0": {
      "status": {
        "state": 20,
        "stateText": "Unavailable",
        "mtu": 1500,
        "deviceType": 1,
        "deviceTypeText": "Ethernet"
      },
      "wired": {
        "permHwAddress": "C0:EE:40:29:C4:F1",
        "speed": 0,
        "carrier": false,
        "hwAddress": "C0:EE:40:29:C4:F1"
      }
    },
    "eth1": {
      "status": {
        "state": 20,
        "stateText": "Unavailable",
        "mtu": 1500,
        "deviceType": 1,
        "deviceTypeText": "Ethernet"
      },
      "wired": {
        "permHwAddress": "C0:EE:40:29:C4:F0",
        "speed": 0,
        "carrier": false,
        "hwAddress": "C0:EE:40:29:C4:F0"
      }
    },
    "wlan0": {
      "status": {
        "state": 30,
        "stateText": "Disconnected",
        "mtu": 1500,
        "deviceType": 2,
        "deviceTypeText": "Wi-Fi"
      },
      "wireless": {
        "bitrate": 0,
        "permHwAddress": "C0:EE:40:43:B6:B4",
        "mode": 2,
        "regDomain": "00",
        "lastScan": 3950074,
        "hwAddress": "C0:EE:40:43:B6:B4"
      }
    },
    "p2p-dev-wlan0": {
      "status": {
        "state": 30,
        "stateText": "Disconnected",
        "mtu": 0,
        "deviceType": 30,
        "deviceTypeText": "WiFi P2P"
      }
    },
    ...
  },
  "devices": 7
}
```

### Connections

#### List all connections
```json
$ ./network_connections_get_all.sh 
=========================
Get all connections
=========================

Status Code: 200
Response:
[
  {
    "id": "lo",
    "uuid": "23f20dd7-4169-4682-af89-a359a7bfbcb4",
    "type": "loopback",
    "activated": true
  },
  ...
]
```

#### List connection by name (id)
```json
$ CONNECTION_NAME="lo" ./network_connections_get_by_id.sh 
=========================
Get connection using connection name (id)
=========================

Connection Name (id): lo
Status Code: 200
Response:
{
  "connection": {
    "auth-retries": -1,
    "autoconnect": false,
    "autoconnect-priority": 0,
    "autoconnect-retries": -1,
    "autoconnect-slaves": -1,
    "dns-over-tls": -1,
    "gateway-ping-timeout": 0,
    "id": "lo",
    "interface-name": "lo",
    "lldp": -1,
    "llmnr": -1,
    "master": null,
    "mdns": -1,
    "metered": 0,
    "mptcp-flags": 0,
    "mud-url": null,
    "multi-connect": 0,
    "permissions": [],
    "read-only": false,
    "secondaries": [],
    "slave-type": null,
    "stable-id": null,
    "timestamp": 1726616978,
    "type": "loopback",
    "uuid": "23f20dd7-4169-4682-af89-a359a7bfbcb4",
    "wait-activation-delay": -1,
    "wait-device-timeout": -1,
    "zone": null
  },
  "ipv4": {
    "addresses": [
      "127.0.0.1/8"
    ],
    "auto-route-ext-gw": -1,
    "dad-timeout": -1,
    "dhcp-hostname": null,
    "dhcp-hostname-flags": 0,
    "dhcp-iaid": null,
    "dhcp-reject-servers": [],
    "dhcp-send-hostname": true,
    "dhcp-timeout": 0,
    "dns": [],
    "dns-options": [],
    "dns-priority": 0,
    "dns-search": [],
    "gateway": null,
    "ignore-auto-dns": false,
    "ignore-auto-routes": false,
    "may-fail": true,
    "method": "manual",
    "never-default": false,
    "required-timeout": -1,
    "route-metric": -1,
    "route-table": 0,
    "routes": [],
    "dhcp-client-id": null,
    "dhcp-fqdn": null,
    "dhcp-vendor-class-identifier": null,
    "link-local": 0,
    "address-data": [
      {
        "address": "127.0.0.1",
        "prefix": 8
      }
    ],
    "route-data": []
  },
  "ipv6": {
    "addresses": [
      "::1/128"
    ],
    "auto-route-ext-gw": -1,
    "dad-timeout": -1,
    "dhcp-hostname": null,
    "dhcp-hostname-flags": 0,
    "dhcp-iaid": null,
    "dhcp-reject-servers": [],
    "dhcp-send-hostname": true,
    "dhcp-timeout": 0,
    "dns": [],
    "dns-options": [],
    "dns-priority": 0,
    "dns-search": [],
    "gateway": null,
    "ignore-auto-dns": false,
    "ignore-auto-routes": false,
    "may-fail": true,
    "method": "manual",
    "never-default": false,
    "required-timeout": -1,
    "route-metric": -1,
    "route-table": 0,
    "routes": [],
    "addr-gen-mode": 3,
    "dhcp-duid": null,
    "ip6-privacy": -1,
    "mtu": 0,
    "ra-timeout": 0,
    "token": null,
    "address-data": [
      {
        "address": "::1",
        "prefix": 128
      }
    ],
    "route-data": []
  },
  "proxy": {
    "browser-only": false,
    "method": 0,
    "pac-script": null,
    "pac-url": null
  },
  "GENERAL": {
    "name": "lo",
    "uuid": "23f20dd7-4169-4682-af89-a359a7bfbcb4",
    "devices": [
      {
        "interface": "lo",
        "ipInterface": "lo"
      }
    ],
    "state": "Activated",
    "default": false,
    "default6": false,
    "specificObjectPath": "/",
    "vpn": false,
    "conPath": "/org/freedesktop/NetworkManager/Settings/4",
    "zone": null,
    "masterPath": "/",
    "dbus-path": "/org/freedesktop/NetworkManager/ActiveConnection/1"
  },
  "IP4": {
    "addressData": [
      {
        "address": "127.0.0.1",
        "prefix": 8
      }
    ],
    "domains": [],
    "gateway": "",
    "dns": [],
    "routeData": []
  },
  "IP6": {
    "addressData": [
      {
        "address": "::1",
        "prefix": 128
      }
    ],
    "domains": [],
    "gateway": "",
    "dns": [],
    "routeData": []
  },
  "DHCP4": {
    "options": []
  },
  "DHCP6": {
    "options": []
  },
  "activated": true
}
```

#### Get connection by UUID
```json
$ UUID="23f20dd7-4169-4682-af89-a359a7bfbcb4" ./network_connections_get_by_uuid.sh 
=========================
Get connection using explicit UUID
=========================

Status Code: 200
Response:
{
  "connection": {
    "auth-retries": -1,
    "autoconnect": false,
    "autoconnect-priority": 0,
    "autoconnect-retries": -1,
    "autoconnect-slaves": -1,
    "dns-over-tls": -1,
    "gateway-ping-timeout": 0,
    "id": "lo",
    "interface-name": "lo",
    "lldp": -1,
    "llmnr": -1,
    "master": null,
    "mdns": -1,
    "metered": 0,
    "mptcp-flags": 0,
    "mud-url": null,
    "multi-connect": 0,
    "permissions": [],
    "read-only": false,
    "secondaries": [],
    "slave-type": null,
    "stable-id": null,
    "timestamp": 1726616978,
    "type": "loopback",
    "uuid": "23f20dd7-4169-4682-af89-a359a7bfbcb4",
    "wait-activation-delay": -1,
    "wait-device-timeout": -1,
    "zone": null
  },
  "ipv4": {
    "addresses": [
      "127.0.0.1/8"
    ],
    "auto-route-ext-gw": -1,
    "dad-timeout": -1,
    "dhcp-hostname": null,
    "dhcp-hostname-flags": 0,
    "dhcp-iaid": null,
    "dhcp-reject-servers": [],
    "dhcp-send-hostname": true,
    "dhcp-timeout": 0,
    "dns": [],
    "dns-options": [],
    "dns-priority": 0,
    "dns-search": [],
    "gateway": null,
    "ignore-auto-dns": false,
    "ignore-auto-routes": false,
    "may-fail": true,
    "method": "manual",
    "never-default": false,
    "required-timeout": -1,
    "route-metric": -1,
    "route-table": 0,
    "routes": [],
    "dhcp-client-id": null,
    "dhcp-fqdn": null,
    "dhcp-vendor-class-identifier": null,
    "link-local": 0,
    "address-data": [
      {
        "address": "127.0.0.1",
        "prefix": 8
      }
    ],
    "route-data": []
  },
  "ipv6": {
    "addresses": [
      "::1/128"
    ],
    "auto-route-ext-gw": -1,
    "dad-timeout": -1,
    "dhcp-hostname": null,
    "dhcp-hostname-flags": 0,
    "dhcp-iaid": null,
    "dhcp-reject-servers": [],
    "dhcp-send-hostname": true,
    "dhcp-timeout": 0,
    "dns": [],
    "dns-options": [],
    "dns-priority": 0,
    "dns-search": [],
    "gateway": null,
    "ignore-auto-dns": false,
    "ignore-auto-routes": false,
    "may-fail": true,
    "method": "manual",
    "never-default": false,
    "required-timeout": -1,
    "route-metric": -1,
    "route-table": 0,
    "routes": [],
    "addr-gen-mode": 3,
    "dhcp-duid": null,
    "ip6-privacy": -1,
    "mtu": 0,
    "ra-timeout": 0,
    "token": null,
    "address-data": [
      {
        "address": "::1",
        "prefix": 128
      }
    ],
    "route-data": []
  },
  "proxy": {
    "browser-only": false,
    "method": 0,
    "pac-script": null,
    "pac-url": null
  },
  "GENERAL": {
    "name": "lo",
    "uuid": "23f20dd7-4169-4682-af89-a359a7bfbcb4",
    "devices": [
      {
        "interface": "lo",
        "ipInterface": "lo"
      }
    ],
    "state": "Activated",
    "default": false,
    "default6": false,
    "specificObjectPath": "/",
    "vpn": false,
    "conPath": "/org/freedesktop/NetworkManager/Settings/4",
    "zone": null,
    "masterPath": "/",
    "dbus-path": "/org/freedesktop/NetworkManager/ActiveConnection/1"
  },
  "IP4": {
    "addressData": [
      {
        "address": "127.0.0.1",
        "prefix": 8
      }
    ],
    "domains": [],
    "gateway": "",
    "dns": [],
    "routeData": []
  },
  "IP6": {
    "addressData": [
      {
        "address": "::1",
        "prefix": 128
      }
    ],
    "domains": [],
    "gateway": "",
    "dns": [],
    "routeData": []
  },
  "DHCP4": {
    "options": []
  },
  "DHCP6": {
    "options": []
  },
  "activated": true
}
```

#### Create connection
```json
$ CONNECTION_NAME="test-connection" SSID="test-ssid" PSK="test-password" ./network_connections_post_PSK.sh 
=========================
Create PSK connection using server-issued UUID
=========================

Connection Name (id): test-connection
SSID: test-ssid
PSK: test-password
Status Code: 201
Response:
{
  "connection": {
    "auth-retries": -1,
    "autoconnect": false,
    "autoconnect-priority": 0,
    "autoconnect-retries": -1,
    "autoconnect-slaves": -1,
    "dns-over-tls": -1,
    "gateway-ping-timeout": 0,
    "id": "test-connection",
    "interface-name": "wlan0",
    "lldp": -1,
    "llmnr": -1,
    "master": null,
    "mdns": -1,
    "metered": 0,
    "mptcp-flags": 0,
    "mud-url": null,
    "multi-connect": 0,
    "permissions": [],
    "read-only": false,
    "secondaries": [],
    "slave-type": null,
    "stable-id": null,
    "timestamp": 1726616978,
    "type": "802-11-wireless",
    "uuid": "83521067-ec0c-469e-b7a7-e73315017d32",
    "wait-activation-delay": -1,
    "wait-device-timeout": -1,
    "zone": null
  },
  "ipv4": {
    "addresses": [],
    "auto-route-ext-gw": -1,
    "dad-timeout": -1,
    "dhcp-hostname": null,
    "dhcp-hostname-flags": 0,
    "dhcp-iaid": null,
    "dhcp-reject-servers": [],
    "dhcp-send-hostname": true,
    "dhcp-timeout": 0,
    "dns": [],
    "dns-options": [],
    "dns-priority": 0,
    "dns-search": [],
    "gateway": null,
    "ignore-auto-dns": false,
    "ignore-auto-routes": false,
    "may-fail": true,
    "method": "auto",
    "never-default": false,
    "required-timeout": -1,
    "route-metric": -1,
    "route-table": 0,
    "routes": [],
    "dhcp-client-id": null,
    "dhcp-fqdn": null,
    "dhcp-vendor-class-identifier": null,
    "link-local": 0,
    "address-data": [],
    "route-data": []
  },
  "ipv6": {
    "addresses": [],
    "auto-route-ext-gw": -1,
    "dad-timeout": -1,
    "dhcp-hostname": null,
    "dhcp-hostname-flags": 0,
    "dhcp-iaid": null,
    "dhcp-reject-servers": [],
    "dhcp-send-hostname": true,
    "dhcp-timeout": 0,
    "dns": [],
    "dns-options": [],
    "dns-priority": 0,
    "dns-search": [],
    "gateway": null,
    "ignore-auto-dns": false,
    "ignore-auto-routes": false,
    "may-fail": true,
    "method": "auto",
    "never-default": false,
    "required-timeout": -1,
    "route-metric": -1,
    "route-table": 0,
    "routes": [],
    "addr-gen-mode": 3,
    "dhcp-duid": null,
    "ip6-privacy": -1,
    "mtu": 0,
    "ra-timeout": 0,
    "token": null,
    "address-data": [],
    "route-data": []
  },
  "proxy": {
    "browser-only": false,
    "method": 0,
    "pac-script": null,
    "pac-url": null
  },
  "802-11-wireless": {
    "ap-isolation": -1,
    "band": null,
    "bssid": null,
    "channel": 0,
    "cloned-mac-address": null,
    "generate-mac-address-mask": null,
    "hidden": false,
    "mac-address": null,
    "mac-address-blacklist": [],
    "mac-address-randomization": 0,
    "mode": "infrastructure",
    "mtu": 0,
    "powersave": 0,
    "rate": 0,
    "seen-bssids": [],
    "ssid": "test-ssid",
    "tx-power": 0,
    "wake-on-wlan": 1,
    "bgscan": "summit:5:-64:30",
    "security": "802-11-wireless-security",
    "RegDomain": "00"
  },
  "802-11-wireless-security": {
    "auth-alg": null,
    "fils": 0,
    "group": [],
    "key-mgmt": "wpa-psk",
    "leap-password": null,
    "leap-password-flags": 0,
    "leap-username": null,
    "pairwise": [],
    "pmf": 0,
    "proto": [],
    "psk": null,
    "psk-flags": 0,
    "wep-key0": null,
    "wep-key1": null,
    "wep-key2": null,
    "wep-key3": null,
    "wep-key-flags": 0,
    "wep-key-type": 0,
    "wep-tx-keyidx": 0,
    "wps-method": 0
  },
  "activated": false
}
```

#### Delete connection
```json
$ CONNECTION_NAME="test-connection" ./network_connections_delete_by_id.sh 
=========================
Delete connection using connection name (id)
=========================

Connection Name (id): test-connection
Status Code: 200
Response:

```

#### Activate/deactivate connection
```json
$ CONNECTION_NAME="test-connection" ACTIVATED="true" ./network_connections_patch_activate_by_id.sh 
=========================
Activate/deactivate connection connection name (id)
=========================

Desired Activation State: true
Connection Name (id): test-connection
Status Code: 200
Response:
{
  "connection": {
    "auth-retries": -1,
    "autoconnect": false,
    "autoconnect-priority": 0,
    "autoconnect-retries": -1,
    "autoconnect-slaves": -1,
    "dns-over-tls": -1,
    "gateway-ping-timeout": 0,
    "id": "test-connection",
    "interface-name": "wlan0",
    "lldp": -1,
    "llmnr": -1,
    "master": null,
    "mdns": -1,
    "metered": 0,
    "mptcp-flags": 0,
    "mud-url": null,
    "multi-connect": 0,
    "permissions": [],
    "read-only": false,
    "secondaries": [],
    "slave-type": null,
    "stable-id": null,
    "timestamp": 1726616978,
    "type": "802-11-wireless",
    "uuid": "aacb3134-591a-48ce-b721-76bd10c6433f",
    "wait-activation-delay": -1,
    "wait-device-timeout": -1,
    "zone": null
  },
  "ipv4": {
    "addresses": [],
    "auto-route-ext-gw": -1,
    "dad-timeout": -1,
    "dhcp-hostname": null,
    "dhcp-hostname-flags": 0,
    "dhcp-iaid": null,
    "dhcp-reject-servers": [],
    "dhcp-send-hostname": true,
    "dhcp-timeout": 0,
    "dns": [],
    "dns-options": [],
    "dns-priority": 0,
    "dns-search": [],
    "gateway": null,
    "ignore-auto-dns": false,
    "ignore-auto-routes": false,
    "may-fail": true,
    "method": "auto",
    "never-default": false,
    "required-timeout": -1,
    "route-metric": -1,
    "route-table": 0,
    "routes": [],
    "dhcp-client-id": null,
    "dhcp-fqdn": null,
    "dhcp-vendor-class-identifier": null,
    "link-local": 0,
    "address-data": [],
    "route-data": []
  },
  "ipv6": {
    "addresses": [],
    "auto-route-ext-gw": -1,
    "dad-timeout": -1,
    "dhcp-hostname": null,
    "dhcp-hostname-flags": 0,
    "dhcp-iaid": null,
    "dhcp-reject-servers": [],
    "dhcp-send-hostname": true,
    "dhcp-timeout": 0,
    "dns": [],
    "dns-options": [],
    "dns-priority": 0,
    "dns-search": [],
    "gateway": null,
    "ignore-auto-dns": false,
    "ignore-auto-routes": false,
    "may-fail": true,
    "method": "auto",
    "never-default": false,
    "required-timeout": -1,
    "route-metric": -1,
    "route-table": 0,
    "routes": [],
    "addr-gen-mode": 3,
    "dhcp-duid": null,
    "ip6-privacy": -1,
    "mtu": 0,
    "ra-timeout": 0,
    "token": null,
    "address-data": [],
    "route-data": []
  },
  "proxy": {
    "browser-only": false,
    "method": 0,
    "pac-script": null,
    "pac-url": null
  },
  "GENERAL": {
    "name": "test-connection",
    "uuid": "aacb3134-591a-48ce-b721-76bd10c6433f",
    "devices": [
      {
        "interface": "wlan0",
        "ipInterface": ""
      }
    ],
    "state": "Activating",
    "default": false,
    "default6": false,
    "specificObjectPath": "/org/freedesktop/NetworkManager/AccessPoint/189",
    "vpn": false,
    "conPath": "/org/freedesktop/NetworkManager/Settings/6",
    "zone": null,
    "masterPath": "/",
    "dbus-path": "/org/freedesktop/NetworkManager/ActiveConnection/4"
  },
  "IP4": {
    "addressData": [],
    "domains": [],
    "gateway": null,
    "dns": [],
    "routeData": []
  },
  "IP6": {
    "addressData": [],
    "domains": [],
    "gateway": null,
    "dns": [],
    "routeData": []
  },
  "DHCP4": {
    "options": []
  },
  "DHCP6": {
    "options": []
  },
  "802-11-wireless": {
    "ap-isolation": -1,
    "band": null,
    "bssid": null,
    "channel": 0,
    "cloned-mac-address": null,
    "generate-mac-address-mask": null,
    "hidden": false,
    "mac-address": null,
    "mac-address-blacklist": [],
    "mac-address-randomization": 0,
    "mode": "infrastructure",
    "mtu": 0,
    "powersave": 0,
    "rate": 0,
    "seen-bssids": [],
    "ssid": "test-ssid",
    "tx-power": 0,
    "wake-on-wlan": 1,
    "bgscan": "summit:5:-64:30",
    "security": "802-11-wireless-security",
    "RegDomain": "00"
  },
  "802-11-wireless-security": {
    "auth-alg": null,
    "fils": 0,
    "group": [],
    "key-mgmt": "wpa-psk",
    "leap-password": null,
    "leap-password-flags": 0,
    "leap-username": null,
    "pairwise": [],
    "pmf": 0,
    "proto": [],
    "psk": null,
    "psk-flags": 0,
    "wep-key0": null,
    "wep-key1": null,
    "wep-key2": null,
    "wep-key3": null,
    "wep-key-flags": 0,
    "wep-key-type": 0,
    "wep-tx-keyidx": 0,
    "wps-method": 0
  },
  "activated": true
}
```

#### Export connections
This endpoint generates a password-protected archive of the current connection profiles.
```json
$ ARCHIVE_PASSWORD="mypassword" ./network_connections_export_get.sh 
=========================
Export network connections
=========================

Archive Path: ./connections.zip
Archive Password: mypassword
Status Code: 200
```
NOTE: Please use a secure password.

#### Import connections
This endpoint accepts a password-protected archive containing connection profiles and imports them for use.
```json
$ ARCHIVE_PASSWORD="mypassword" ./network_connections_import_put.sh 
=========================
Import network connections
=========================

Archive Path: ./connections.zip
Archive Password: mypassword
Overwrite Existing: false
Status Code: 200
Response:
```

### Certificates

#### List all certificates
```json
$ ./network_certificates_get_all.sh 
=========================
Get all certificates
=========================

Status Code: 200
Response:
[
  "test.crt"
]
```

#### Get certificate details
```json
$ CERT_NAME="test.crt" ./network_certificates_get.sh 
=========================
Get certificate info
=========================

Certificate Name: test.crt
Status Code: 200
Response:
{
  "version": 3,
  "serial_number": "14178481360375830430",
  "subject": "/C=US/ST=OH/L=Akron/O=Ezurio/OU=Engineering/CN=Summit/emailAddress=info@ezurio.com",
  "issuer": "/C=US/ST=OH/L=Akron/O=Ezurio/OU=Engineering/CN=www.ezurio.com/emailAddress=info@ezurio.com",
  "not_before": "Jun 11 01:54:01 2024 GMT",
  "not_after": "Jun  9 01:54:01 2034 GMT",
  "extensions": [
    {
      "name": "X509v3 Authority Key Identifier",
      "value": "DirName:/C=US/ST=OH/L=Akron/O=Ezurio/OU=Engineering/CN=www.ezurio.com/emailAddress=info@ezurio.com\nserial:42:C9:05:62:2A:88:FF:11:C9:17:AE:47:BD:04:6B:07:DD:7D:3E:98\n"
    },
    {
      "name": "X509v3 Key Usage",
      "value": "Digital Signature, Non Repudiation, Key Encipherment, Data Encipherment"
    },
    {
      "name": "X509v3 Subject Alternative Name",
      "value": "DNS:test.summit.com, DNS:*.summit.com"
    },
    {
      "name": "X509v3 Subject Key Identifier",
      "value": "CB:A0:50:F9:B5:B3:A8:3D:54:EB:E7:E1:07:45:2E:C6:6E:59:93:E9"
    }
  ]
}
```

#### Add certificate
```json
$ FILE_NAME="test.crt" FILE_PATH="/path/to/certificate.crt" ./network_certificates_post.sh 
=========================
Upload certificate or PAC file for use by NetworkManager
=========================

File Name: test.crt
File Path: /path/to/certificate.crt
Status Code: 201
Response:
```

#### Delete certificate
```json
$ CERT_NAME="test.crt" ./network_certificates_delete.sh 
=========================
Remove certificate
=========================

Certificate Name: test.crt
Status Code: 200
Response:
```

### Interfaces

#### List all interfaces
```json
$ ./network_interfaces_get_all.sh 
=========================
Get all network interfaces
=========================

Status Code: 200
Response:
[
  "lo",
  "eth0",
  "eth1",
  "wlan0",
  ...
]
```


#### Get interface details
```json
$ NAME="wlan0" ./network_interfaces_get_by_name.sh 
=========================
Get network interface info by name
=========================

Interface Name: wlan0
Status Code: 200
Response:
{
  "status": {
    "state": 30,
    "stateText": "Disconnected",
    "mtu": 1500,
    "deviceType": 2,
    "deviceTypeText": "Wi-Fi"
  },
  "wireless": {
    "bitrate": 0,
    "permHwAddress": "C0:EE:40:43:B6:B4",
    "mode": 2,
    "regDomain": "00",
    "lastScan": 5574220,
    "hwAddress": "C0:EE:40:43:B6:B4"
  },
  "udi": "/sys/devices/platform/ahb/ahb:apb/f8000000.mmc/mmc_host/mmc1/mmc1:0001/mmc1:0001:1/net/wlan0",
  "path": "/org/freedesktop/NetworkManager/Devices/5",
  "interface": "wlan0",
  "ipInterface": "",
  "driver": "lrdmwl_sdio",
  "driverVersion": "4.19.203",
  "firmwareVersion": "N/A",
  "capabilities": 1,
  "stateReason": 0,
  "activeConnection": {},
  "managed": true,
  "autoconnect": true,
  "firmwareMissing": false,
  "nmPluginMissing": false,
  "availableConnections": [],
  "physicalPortId": "",
  "metered": 0,
  "meteredText": "Unknown",
  "lldpNeighbors": [],
  "real": true,
  "ip4Connectivity": 1,
  "ip4ConnectivityText": "None",
  "ip6Connectivity": 1,
  "ip6ConnectivityText": "None",
  "interfaceFlags": 1
}
```

#### Get interface statistics
```json
$ NAME="wlan0" ./network_interfaces_stats_get.sh 
=========================
Get network interface stats by name
=========================

Interface Name: wlan0
Status Code: 200
Response:
{
  "rxBytes": 0,
  "rxPackets": 0,
  "rxErrors": 0,
  "rxDropped": 0,
  "multicast": 0,
  "txBytes": 0,
  "txPackets": 0,
  "txErrors": 0,
  "txDropped": 0
}
```

#### Get interface station dump
```json
$ NAME="wlan0" ./network_interfaces_station_dump_get.sh 
=========================
Get network interface station dump by name
=========================

Interface Name: wlan0
Status Code: 200
Response:
{
  "00:21:6a:fa:c2:f6": {
    "signal": -23,
    "inactive": 20,
    "connectedTime": 306,
    "rxPackets": 21566,
    "txPackets": 36093,
    "beaconRx": null,
    "rxRate": {
      "rate": 144400,
      "channelWidth": 20
    },
    "txRate": {
      "rate": 1000,
      "channelWidth": 20
    },
    "rxBytes": 6759192,
    "txBytes": 40007325,
    "rxDuration": 0,
    "txRetries": 0,
    "txFailed": 0,
    "beaconLoss": null,
    "rxDropMisc": 0,
    "dtimPeriod": 2,
    "beaconInterval": 100
  },
  ...
}
```
NOTE: The station dump information is not guaranteed to be always correct.

#### Get interface available AP channels
```json
$ NAME="wlan0" ./network_interfaces_available_ap_channels_get.sh 
=========================
Get the available AP mode channels for the network interface
=========================

Interface Name: wlan0
Status Code: 200
Response:
[
  {
    "channel": 1,
    "frequency": 2412
  },
  {
    "channel": 2,
    "frequency": 2417
  },
  {
    "channel": 3,
    "frequency": 2422
  },
  {
    "channel": 4,
    "frequency": 2427
  },
  {
    "channel": 5,
    "frequency": 2432
  },
  {
    "channel": 6,
    "frequency": 2437
  },
  {
    "channel": 7,
    "frequency": 2442
  },
  {
    "channel": 8,
    "frequency": 2447
  },
  {
    "channel": 9,
    "frequency": 2452
  },
  {
    "channel": 10,
    "frequency": 2457
  },
  {
    "channel": 11,
    "frequency": 2462
  }
]
```

#### Get interface DHCP leases
```json
$ NAME="wlan0" ./network_interfaces_dhcp_leases.sh 
=========================
Get the current DHCP leases for the network interface
=========================

Interface Name: wlan0
Status Code: 200
Response:
{
  "ipv4": [
    {
      "expiry": 1726626663,
      "macAddress": "00:21:6a:fa:c2:f6",
      "ipAddress": "172.16.54.210",
      "hostname": "HOSTNAME1",
      "clientIdentifer": "01:00:21:6a:fa:c2:f6"
    },
    {
      "expiry": 1726625583,
      "macAddress": "de:ad:be:ef:00:00",
      "ipAddress": "172.16.54.203",
      "hostname": "HOSTNAME2",
      "clientIdentifer": "01:de:ad:be:ef:00:00"
    }
  ],
  "ipv6": [
    {
      "expiry": 1726709463,
      "iaid": "134226282",
      "ipAddress": "2001:db8::f5",
      "hostname": "HOSTNAME1",
      "clientDuid": "00:01:00:01:2c:09:b2:0f:d0:94:66:fe:12:1a"
    }
  ]
}
```

#### Get interface driver info
```json
$ NAME="wlan0" ./network_interfaces_driver_info_get.sh 
=========================
Get network interface driver info by name
=========================

Interface Name: wlan0
Status Code: 200
Response:
{
  "adoptedCountryCode": "00",
  "otpCountryCode": "00"
}
```

#### Add virtual interface
```json
$ ./network_interfaces_virtual_add.sh 
=========================
Add virtual network interface (wlan1)
=========================

Status Code: 201
Response:
{
  "status": {
    "state": 30,
    "stateText": "Disconnected",
    "mtu": 1500,
    "deviceType": 2,
    "deviceTypeText": "Wi-Fi"
  },
  "wireless": {
    "bitrate": 0,
    "permHwAddress": "C0:EE:40:43:B6:B5",
    "mode": 2,
    "regDomain": "00",
    "lastScan": 183299,
    "hwAddress": "C0:EE:40:43:B6:B5"
  },
  "udi": "/sys/devices/platform/ahb/ahb:apb/f8000000.mmc/mmc_host/mmc1/mmc1:0001/mmc1:0001:1/net/wlan1",
  "path": "/org/freedesktop/NetworkManager/Devices/8",
  "interface": "wlan1",
  "ipInterface": "",
  "driver": "lrdmwl_sdio",
  "driverVersion": "4.19.203",
  "firmwareVersion": "N/A",
  "capabilities": 1,
  "stateReason": 42,
  "activeConnection": {},
  "managed": true,
  "autoconnect": true,
  "firmwareMissing": false,
  "nmPluginMissing": false,
  "availableConnections": [],
  "physicalPortId": "",
  "metered": 0,
  "meteredText": "Unknown",
  "lldpNeighbors": [],
  "real": true,
  "ip4Connectivity": 1,
  "ip4ConnectivityText": "None",
  "ip6Connectivity": 1,
  "ip6ConnectivityText": "None",
  "interfaceFlags": 1
}
```

#### Remove virtual interface
```json
$ ./network_interfaces_virtual_remove.sh 
=========================
Remove virtual network interface (wlan1)
=========================

Status Code: 200
Response:
```

### Access Points

#### List all known access points
```json
$ ./network_access_points_get.sh 
=========================
Get access points
=========================

Status Code: 200
Response:
[
  {
    "ssid": "WEP-network",
    "hwAddress": "62:45:B0:31:B6:7A",
    "strength": 29,
    "maxBitrate": 0,
    "frequency": 5200,
    "flags": 1,
    "wpaFlags": 0,
    "rsnFlags": 0,
    "lastSeen": 451,
    "security": "WEP",
    "keymgmt": "static"
  },
  {
    "ssid": "open-network",
    "hwAddress": "C4:E9:84:87:59:16",
    "strength": 100,
    "maxBitrate": 130000,
    "frequency": 2432,
    "flags": 0,
    "wpaFlags": 0,
    "rsnFlags": 0,
    "lastSeen": 449,
    "security": "",
    "keymgmt": "none"
  },
  {
    "ssid": "EAP-network",
    "hwAddress": "2E:AB:F8:AE:8F:DA",
    "strength": 19,
    "maxBitrate": 540000,
    "frequency": 5785,
    "flags": 1,
    "wpaFlags": 0,
    "rsnFlags": 648,
    "lastSeen": 458,
    "security": "WPA2 802.1X",
    "keymgmt": "wpa-eap"
  },
  {
    "ssid": "WPA2-PSK-network",
    "hwAddress": "78:24:AF:D2:C7:10",
    "strength": 59,
    "maxBitrate": 195000,
    "frequency": 2457,
    "flags": 1,
    "wpaFlags": 0,
    "rsnFlags": 392,
    "lastSeen": 458,
    "security": "WPA2 PSK",
    "keymgmt": "wpa-psk"
  },
  ...
]
```

#### Request scan
```json
$ ./network_access_points_put.sh 
=========================
Request scan for access points
=========================

Status Code: 200
Response:
{
  "scanRequested": true
}
```

#### Get seconds since last scan
```json
$ ./network_access_points_get_seconds_since_last_scan.sh 
=========================
Get seconds since last access point scan
=========================

Status Code: 200
Response:
{
  "secondsSinceLastScan": 28
}
```

## Wi-Fi
Settings and control for the Wi-Fi radio

### Get current settings
```json$ ./network_wifi_get.sh 
=========================
Get Wi-Fi settings
=========================

Status Code: 200
Response:
{
  "wifiRadioSoftwareEnabled": true,
  "wifiRadioHardwareEnabled": true
}
```

### Software enable/disable radio
```json
$ WIFI_RADIO_SOFTWARE_ENABLED="false" ./network_wifi_put.sh 
=========================
Set Wi-Fi settings
=========================

Desired Wi-Fi Radio Software Enabled: false
Desired Wi-Fi Radio Hardware Enabled: true
Status Code: 200
Response:
{
  "wifiRadioSoftwareEnabled": false,
  "wifiRadioHardwareEnabled": true
}
```

## System

### Version

#### Get version info
```json
$ ./system_version_get.sh 
=========================
Get system version info
=========================

Status Code: 200
Response:
{
  "nmVersion": "12.0.0.113-1.46.2",
  "summitRcm": "12.0.0.153",
  "build": "Summit Linux development build 0.12.0.0",
  "supplicant": "12.0.0.113-40.3.25.3",
  "radioStack": "12.0.0.113",
  "driver": "lrdmwl_sdio",
  "kernelVermagic": "4.19.203",
  "bluez": "5.72",
  "uBoot": "2024.04-12.0.0.138-som60sd",
  "currentSide": "a",
  "baseHwPartNumber": "453-00004",
  "nextSide": "a"
}
```

### Date/Time

#### Get current date/time/timezone
```json
$ ./system_datetime_get.sh 
=========================
Get Date/Time/Timezone
=========================

Status Code: 200
Response:
{
  "zones": [
    ...
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
    ...
    "Pacific/Palau",
    "Pacific/Pitcairn",
    "Pacific/Port_Moresby",
    "Pacific/Rarotonga",
    "Pacific/Tahiti",
    "Pacific/Tarawa",
    "Pacific/Tongatapu",
    "UTC"
  ],
  "zone": "Etc/UTC",
  "datetime": "2025-02-19 15:00:42"
}
```

#### Set current date/time/timezone
```json
$ ./system_datetime_put.sh 
=========================
Set Date/Time/Timezone
=========================

Datetime: 1739977395228275
Timezone: Etc/UTC
Status Code: 200
Response:
{
  "zones": [
    ...
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
    ...
    "Pacific/Palau",
    "Pacific/Pitcairn",
    "Pacific/Port_Moresby",
    "Pacific/Rarotonga",
    "Pacific/Tahiti",
    "Pacific/Tarawa",
    "Pacific/Tongatapu",
    "UTC"
  ],
  "zone": "Etc/UTC",
  "datetime": "2025-02-19 15:03:15"
}
```
NOTE: The expected unit for the `datetime` parameter is microseconds.

### Logs

#### Retrieve log data
```json
=========================
Get log data
=========================

Log Type: All
Priority: 6
Days: -1
Status Code: 200
[
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
  ...
]
```

#### Export log data
This endpoint generates a password-protected archive of the module's system logs
```json
$ ARCHIVE_PASSWORD="mypassword" ./system_logs_export_get.sh 
=========================
Export logs
=========================

Archive Path: ./logs.zip
Archive Password: mypassword
Status Code: 200
```

#### Get log configuration
```json
$ ./system_logs_config_get.sh 
=========================
Get log configuration
=========================

Status Code: 200
{
  "suppDebugLevel": "none",
  "driverDebugLevel": 0
}
```

#### Set log configuration
Valid supplicant debug levels:
- none (default)
- error
- warning
- info
- debug
- msgdump
- excessive

Valid Wi-Fi driver debug levels:
- 0 (default)
- 1
```json
$ SUPPLICANT_DEBUG_LEVEL="info" WIFI_DRIVER_DEBUG_LEVEL=1 ./system_logs_config_set.sh 
=========================
Set log configuration
=========================

Supplicant Debug Level: info
Wi-Fi Driver Debug Level: 1
Status Code: 200
{
  "suppDebugLevel": "info",
  "driverDebugLevel": 1
}
```

#### Get webserver log level
```json
$ ./system_logs_webserver_get.sh 
=========================
Get webserver log level
=========================

Status Code: 200
{
  "webserverLogLevel": "error"
}
```

#### Set webserver log level
Valid webserver log levels:
- critical
- error (default)
- warning
- info
- debug
- trace
```json
$ WEBSERVER_LOG_LEVEL="trace" ./system_logs_webserver_set.sh 
=========================
Set webserver log level
=========================

Webserver Log Level: trace
Status Code: 200
{
  "webserverLogLevel": "trace"
}
```

### FIPS

#### Get current FIPS status
```json
$ ./system_fips_get.sh 
=========================
Get current FIPS status
=========================

Status Code: 200
Response:
{
  "state": "unset"
}
```

#### Set current FIPS status
Valid FIPS states:
- unset (default)
- fips
- fipsWifi
```json
$ DESIRED_STATE="fipsWifi" ./system_fips_set.sh 
=========================
Set current FIPS status
=========================

Desired FIPS State: fipsWifi
Status Code: 200
Response:
{
  "state": "unset"
}
```
NOTE: Changes to the FIPS state take affect after a reboot. Therefore, the `state` value in the reponse will not change immediately.

### Power

#### Get system power status
```json
$ ./system_power_status_get.sh 
=========================
Get system power status
=========================

Status Code: 200
Response:
{
  "state": "on"
}
```

#### Suspend
```json
$ ./system_power_suspend.sh 
=========================
Suspend
=========================

Status Code: 200
Response:
{
  "state": "suspend"
}
```

#### Reboot
```json
$ ./system_power_reboot.sh 
=========================
Reboot
=========================

Status Code: 200
Response:
{
  "state": "reboot"
}
```

#### Power off
```json
$ ./system_power_off.sh 
=========================
Power off
=========================

Status Code: 200
Response:
{
  "state": "off"
}
```

### Factory Reset

#### Initiate factory reset
```json
$ ./system_power_off.sh 
=========================
Initiate Factory Reset
=========================

Status Code: 200
Response:
{
  "initiateFactoryReset": true,
  "autoReboot": false
}
```
NOTE: Factory reset is only available when the system is NOT running from SD card.

NOTE: Unless the `autoReboot` parameter is set to `true`, the module must be manually rebooted to complete the factory reset.

### Firmware Update

#### Get current update status
```json
$ ./system_update_status_get.sh 
=========================
Get current update status
=========================

Status Code: 200
Response:
{
  "status": 2,
  "url": "",
  "image": ""
}
```

#### Set current update status
This endpoint can be used to initiate a firmware update or cancel an in-progress update.

Valid update statuses are:
- 0 (Updated)
- 1 (Fail)
- 2 (Not updating)
- 5 (Updating)
```json
$ DESIRED_STATUS=2 ./system_update_status_set.sh 
=========================
Set current update status
=========================

Desired update status: 2
Firmware URL: 
Image: full
Status Code: 200
Response:
{
  "status": 2,
  "url": "",
  "image": ""
}
```

#### Streaming update (recommended)
Perform a firmware update where the firmware update file is streamed to the module.
```json
$ ./system_update_streaming.sh "/path/to/firmware_update.swu" 
=========================
System update (streaming)
=========================

=========================
Cancel any in-progress update
=========================

Status Code: 200
Response:
{
  "status": 2,
  "url": "",
  "image": ""
}

=========================
Initiate update
=========================

Firmware: /path/to/firmware_update.swu
Image: full
Status Code: 200
Response:
{
  "status": 5,
  "url": "",
  "image": "full"
}

=========================
Send update file
=========================

Status Code: 200
Response:


=========================
Check status
=========================

Status Code: 200
Response:
{
  "status": 5,
  "url": "",
  "image": "full"
}

...

=========================
Check status
=========================

Status Code: 200
Response:
{
  "status": 0,
  "url": "",
  "image": ""
}

=========================
Reboot
=========================

Status Code: 200
Response:
{
  "state": "reboot"
}

Done
```
NOTE: The firmware update requires a reboot of the module. This example script initiates the reboot automatically when the update is successful.

#### Block mode update
Perform a firmware update where the firmware update file is sliced into smaller pieces before being sent to the module.
```json
$ ./system_update_block_mode.sh "/path/to/firmware_update.swu"
=========================
System update (block mode)
=========================

=========================
Cancel any in-progress update
=========================

Status Code: 200
Response:
{
  "status": 2,
  "url": "",
  "image": ""
}

=========================
Initiate update
=========================

Firmware: /path/to/firmware_update.swu
Image: full
Status Code: 200
Response:
{
  "status": 5,
  "url": "",
  "image": "full"
}

=========================
Send chunks
=========================

Sending: x0000.swu-block
  Status Code: 200
  Response:

Sending: x0001.swu-block
  Status Code: 200
  Response:

...

Sending: x0332.swu-block
  Status Code: 200
  Response:


=========================
Check status
=========================

Status Code: 200
Response:
{
  "status": 5,
  "url": "",
  "image": "full"
}

...

=========================
Check status
=========================

Status Code: 200
Response:
{
  "status": 0,
  "url": "",
  "image": ""
}

=========================
Reboot
=========================

Status Code: 200
Response:
{
  "state": "reboot"
}

Done
```
NOTE: The firmware update requires a reboot of the module. This example script initiates the reboot automatically when the update is successful.

#### Server pull update
Perform a firmware update where the module retrieves the firmware update file from a provided URL. The module must be able to access and download the file using a supported protocol (e.g., HTTP, FTP, etc.).
```json
$ ./system_update_server_pull.sh http://192.168.1.2/firmware_update.swu
=========================
System update (server pull)
=========================

=========================
Initiate update
=========================

Firmware URL: http://192.168.1.2/firmware_update.swu
Image: full
Status Code: 200
Response:
{
  "status": 5,
  "url": "http://192.168.1.2/firmware_update.swu",
  "image": "full"
}

=========================
Check status
=========================

Status Code: 200
Response:
{
  "status": 5,
  "url": "http://192.168.1.2/firmware_update.swu",
  "image": "full"
}

...

=========================
Check status
=========================

Status Code: 200
Response:
{
  "status": 0,
  "url": "",
  "image": ""
}

=========================
Reboot
=========================

Status Code: 200
Response:
{
  "state": "reboot"
}

Done
```
NOTE: The firmware update requires a reboot of the module. This example script initiates the reboot automatically when the update is successful.

### Configuration Import/Export

#### Export configuration
This endpoint generates a password-protected archive of the system configuration.
```json
$ ARCHIVE_PASSWORD="mypassword" ./system_config_export_get.sh 
=========================
Export system configuration
=========================

Archive Path: ./config.zip
Archive Password: mypassword
Status Code: 200
```
NOTE: Please use a secure password.

#### Import configuration
This endpoints accepts a password-protected archive of the system configurartion and applies it.
```json
$ ARCHIVE_PASSWORD="mypassword" ./system_config_import_put.sh 
=========================
Import system configuration
=========================

Archive Path: ./config.zip
Archive Password: mypassword
Status Code: 200
Response:
```
NOTE: Please use a secure password.

#### Debug export
This endpoint generates an encrypted archive of the relevant system logs and configuration for debug purposes. The archive is encrypted with the certificate used to facilitate HTTPS/SSL communication on the module, and the server key/certificate pair are required to decrypt the archive.
```json
$ ./system_debug_export_get.sh 
=========================
Export debug info
=========================

Archive Path: ./debug.encrypt
Status Code: 200

./debug.encrypt file downloaded. To decrypt:
openssl cms -decrypt -in ./debug.encrypt -recip /path/to/server.crt -inkey /path/to/server.key -out debug.zip -inform DER
```
