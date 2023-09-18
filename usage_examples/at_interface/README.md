This is a set of scripts which can be used for testing/verification and examples of usage for the various AT interface commands.

The at_interface_settings define the global settings for all AT scripts with certain defaults set automatically. The network connection ID and password is blank by default and must be set to the appropriate values based on the network you're trying to connect to. The firmware update file name and size are also blank by default and must be set before running the firmware updates script. The device will need to be changed to the proper port and use the dependent Windows/Linux naming convention. Any other changes in settings must be made manually as well by editing the settings file. 

All scripts can be run by opening a terminal in the at_interface usage examples directory and running "python .\{name_of_script}.py" on Windows or "python {name_of_script}.py" in Linux. 

# System Settings

### python .\system_setting.py
    ATE1
    OK

    ATE0
    OK

    AT
    OK

    AT+VER
    +VER: 11.0.0.122
    OK

    AT+NTPGET
    +NTPGET: time.nist.gov,static
    OK

    AT+TZGET
    +TZGET: Etc/UTC
    OK

    AT+TZGET=1
    +TZGET: Africa/Abidjan
    +TZGET: Africa/Algiers
    +TZGET: Africa/Bissau
    +TZGET: Africa/Cairo
    +TZGET: Africa/Casablanca
    +TZGET: Africa/Ceuta
    +TZGET: Africa/El_Aaiun
    +TZGET: Africa/Johannesburg
    +TZGET: Africa/Juba
    +TZGET: Africa/Khartoum
    +TZGET: Africa/Lagos
    +TZGET: Africa/Maputo
    +TZGET: Africa/Monrovia
    +TZGET: Africa/Nairobi
    +TZGET: Africa/Ndjamena
    +TZGET: Africa/Sao_Tome
    +TZGET: Africa/Tripoli
    +TZGET: Africa/Tunis
    +TZGET: Africa/Windhoek
    +TZGET: America/Adak
    +TZGET: America/Anchorage
    +TZGET: America/Araguaina
    +TZGET: America/Argentina/Buenos_Aires
    +TZGET: America/Argentina/Catamarca
    +TZGET: America/Argentina/Cordoba
    +TZGET: America/Argentina/Jujuy
    +TZGET: America/Argentina/La_Rioja
    +TZGET: America/Argentina/Mendoza
    +TZGET: America/Argentina/Rio_Gallegos
    +TZGET: America/Argentina/Salta
    +TZGET: America/Argentina/San_Juan
    +TZGET: America/Argentina/San_Luis
    +TZGET: America/Argentina/Tucuman
    +TZGET: America/Argentina/Ushuaia
    +TZGET: America/Asuncion
    +TZGET: America/Bahia
    +TZGET: America/Bahia_Banderas
    +TZGET: America/Barbados
    +TZGET: America/Belem
    +TZGET: America/Belize
    +TZGET: America/Boa_Vista
    +TZGET: America/Bogota
    +TZGET: America/Boise
    +TZGET: America/Cambridge_Bay
    +TZGET: America/Campo_Grande
    +TZGET: America/Cancun
    +TZGET: America/Caracas
    +TZGET: America/Cayenne
    +TZGET: America/Chicago
    +TZGET: America/Chihuahua
    +TZGET: America/Ciudad_Juarez
    +TZGET: America/Costa_Rica
    +TZGET: America/Cuiaba
    +TZGET: America/Danmarkshavn
    +TZGET: America/Dawson
    +TZGET: America/Dawson_Creek
    +TZGET: America/Denver
    +TZGET: America/Detroit
    +TZGET: America/Edmonton
    +TZGET: America/Eirunepe
    +TZGET: America/El_Salvador
    +TZGET: America/Fort_Nelson
    +TZGET: America/Fortaleza
    +TZGET: America/Glace_Bay
    +TZGET: America/Goose_Bay
    +TZGET: America/Grand_Turk
    +TZGET: America/Guatemala
    +TZGET: America/Guayaquil
    +TZGET: America/Guyana
    +TZGET: America/Halifax
    +TZGET: America/Havana
    +TZGET: America/Hermosillo
    +TZGET: America/Indiana/Indianapolis
    +TZGET: America/Indiana/Knox
    +TZGET: America/Indiana/Marengo
    +TZGET: America/Indiana/Petersburg
    +TZGET: America/Indiana/Tell_City
    +TZGET: America/Indiana/Vevay
    +TZGET: America/Indiana/Vincennes
    +TZGET: America/Indiana/Winamac
    +TZGET: America/Inuvik
    +TZGET: America/Iqaluit
    +TZGET: America/Jamaica
    +TZGET: America/Juneau
    +TZGET: America/Kentucky/Louisville
    +TZGET: America/Kentucky/Monticello
    +TZGET: America/La_Paz
    +TZGET: America/Lima
    +TZGET: America/Los_Angeles
    +TZGET: America/Maceio
    +TZGET: America/Managua
    +TZGET: America/Manaus
    +TZGET: America/Martinique
    +TZGET: America/Matamoros
    +TZGET: America/Mazatlan
    +TZGET: America/Menominee
    +TZGET: America/Merida
    +TZGET: America/Metlakatla
    +TZGET: America/Mexico_City
    +TZGET: America/Miquelon
    +TZGET: America/Moncton
    +TZGET: America/Monterrey
    +TZGET: America/Montevideo
    +TZGET: America/New_York
    +TZGET: America/Nome
    +TZGET: America/Noronha
    +TZGET: America/North_Dakota/Beulah
    +TZGET: America/North_Dakota/Center
    +TZGET: America/North_Dakota/New_Salem
    +TZGET: America/Nuuk
    +TZGET: America/Ojinaga
    +TZGET: America/Panama
    +TZGET: America/Paramaribo
    +TZGET: America/Phoenix
    +TZGET: America/Port-au-Prince
    +TZGET: America/Porto_Velho
    +TZGET: America/Puerto_Rico
    +TZGET: America/Punta_Arenas
    +TZGET: America/Rankin_Inlet
    +TZGET: America/Recife
    +TZGET: America/Regina
    +TZGET: America/Resolute
    +TZGET: America/Rio_Branco
    +TZGET: America/Santarem
    +TZGET: America/Santiago
    +TZGET: America/Santo_Domingo
    +TZGET: America/Sao_Paulo
    +TZGET: America/Scoresbysund
    +TZGET: America/Sitka
    +TZGET: America/St_Johns
    +TZGET: America/Swift_Current
    +TZGET: America/Tegucigalpa
    +TZGET: America/Thule
    +TZGET: America/Tijuana
    +TZGET: America/Toronto
    +TZGET: America/Vancouver
    +TZGET: America/Whitehorse
    +TZGET: America/Winnipeg
    +TZGET: America/Yakutat
    +TZGET: Antarctica/Casey
    +TZGET: Antarctica/Davis
    +TZGET: Antarctica/Macquarie
    +TZGET: Antarctica/Mawson
    +TZGET: Antarctica/Palmer
    +TZGET: Antarctica/Rothera
    +TZGET: Antarctica/Troll
    +TZGET: Asia/Almaty
    +TZGET: Asia/Amman
    +TZGET: Asia/Anadyr
    +TZGET: Asia/Aqtau
    +TZGET: Asia/Aqtobe
    +TZGET: Asia/Ashgabat
    +TZGET: Asia/Atyrau
    +TZGET: Asia/Baghdad
    +TZGET: Asia/Baku
    +TZGET: Asia/Bangkok
    +TZGET: Asia/Barnaul
    +TZGET: Asia/Beirut
    +TZGET: Asia/Bishkek
    +TZGET: Asia/Chita
    +TZGET: Asia/Choibalsan
    +TZGET: Asia/Colombo
    +TZGET: Asia/Damascus
    +TZGET: Asia/Dhaka
    +TZGET: Asia/Dili
    +TZGET: Asia/Dubai
    +TZGET: Asia/Dushanbe
    +TZGET: Asia/Famagusta
    +TZGET: Asia/Gaza
    +TZGET: Asia/Hebron
    +TZGET: Asia/Ho_Chi_Minh
    +TZGET: Asia/Hong_Kong
    +TZGET: Asia/Hovd
    +TZGET: Asia/Irkutsk
    +TZGET: Asia/Jakarta
    +TZGET: Asia/Jayapura
    +TZGET: Asia/Jerusalem
    +TZGET: Asia/Kabul
    +TZGET: Asia/Kamchatka
    +TZGET: Asia/Karachi
    +TZGET: Asia/Kathmandu
    +TZGET: Asia/Khandyga
    +TZGET: Asia/Kolkata
    +TZGET: Asia/Krasnoyarsk
    +TZGET: Asia/Kuching
    +TZGET: Asia/Macau
    +TZGET: Asia/Magadan
    +TZGET: Asia/Makassar
    +TZGET: Asia/Manila
    +TZGET: Asia/Nicosia
    +TZGET: Asia/Novokuznetsk
    +TZGET: Asia/Novosibirsk
    +TZGET: Asia/Omsk
    +TZGET: Asia/Oral
    +TZGET: Asia/Pontianak
    +TZGET: Asia/Pyongyang
    +TZGET: Asia/Qatar
    +TZGET: Asia/Qostanay
    +TZGET: Asia/Qyzylorda
    +TZGET: Asia/Riyadh
    +TZGET: Asia/Sakhalin
    +TZGET: Asia/Samarkand
    +TZGET: Asia/Seoul
    +TZGET: Asia/Shanghai
    +TZGET: Asia/Singapore
    +TZGET: Asia/Srednekolymsk
    +TZGET: Asia/Taipei
    +TZGET: Asia/Tashkent
    +TZGET: Asia/Tbilisi
    +TZGET: Asia/Tehran
    +TZGET: Asia/Thimphu
    +TZGET: Asia/Tokyo
    +TZGET: Asia/Tomsk
    +TZGET: Asia/Ulaanbaatar
    +TZGET: Asia/Urumqi
    +TZGET: Asia/Ust-Nera
    +TZGET: Asia/Vladivostok
    +TZGET: Asia/Yakutsk
    +TZGET: Asia/Yangon
    +TZGET: Asia/Yekaterinburg
    +TZGET: Asia/Yerevan
    +TZGET: Atlantic/Azores
    +TZGET: Atlantic/Bermuda
    +TZGET: Atlantic/Canary
    +TZGET: Atlantic/Cape_Verde
    +TZGET: Atlantic/Faroe
    +TZGET: Atlantic/Madeira
    +TZGET: Atlantic/South_Georgia
    +TZGET: Atlantic/Stanley
    +TZGET: Australia/Adelaide
    +TZGET: Australia/Brisbane
    +TZGET: Australia/Broken_Hill
    +TZGET: Australia/Darwin
    +TZGET: Australia/Eucla
    +TZGET: Australia/Hobart
    +TZGET: Australia/Lindeman
    +TZGET: Australia/Lord_Howe
    +TZGET: Australia/Melbourne
    +TZGET: Australia/Perth
    +TZGET: Australia/Sydney
    +TZGET: Europe/Andorra
    +TZGET: Europe/Astrakhan
    +TZGET: Europe/Athens
    +TZGET: Europe/Belgrade
    +TZGET: Europe/Berlin
    +TZGET: Europe/Brussels
    +TZGET: Europe/Bucharest
    +TZGET: Europe/Budapest
    +TZGET: Europe/Chisinau
    +TZGET: Europe/Dublin
    +TZGET: Europe/Gibraltar
    +TZGET: Europe/Helsinki
    +TZGET: Europe/Istanbul
    +TZGET: Europe/Kaliningrad
    +TZGET: Europe/Kirov
    +TZGET: Europe/Kyiv
    +TZGET: Europe/Lisbon
    +TZGET: Europe/London
    +TZGET: Europe/Madrid
    +TZGET: Europe/Malta
    +TZGET: Europe/Minsk
    +TZGET: Europe/Moscow
    +TZGET: Europe/Paris
    +TZGET: Europe/Prague
    +TZGET: Europe/Riga
    +TZGET: Europe/Rome
    +TZGET: Europe/Samara
    +TZGET: Europe/Saratov
    +TZGET: Europe/Simferopol
    +TZGET: Europe/Sofia
    +TZGET: Europe/Tallinn
    +TZGET: Europe/Tirane
    +TZGET: Europe/Ulyanovsk
    +TZGET: Europe/Vienna
    +TZGET: Europe/Vilnius
    +TZGET: Europe/Volgograd
    +TZGET: Europe/Warsaw
    +TZGET: Europe/Zurich
    +TZGET: Indian/Chagos
    +TZGET: Indian/Maldives
    +TZGET: Indian/Mauritius
    +TZGET: Pacific/Apia
    +TZGET: Pacific/Auckland
    +TZGET: Pacific/Bougainville
    +TZGET: Pacific/Chatham
    +TZGET: Pacific/Easter
    +TZGET: Pacific/Efate
    +TZGET: Pacific/Fakaofo
    +TZGET: Pacific/Fiji
    +TZGET: Pacific/Galapagos
    +TZGET: Pacific/Gambier
    +TZGET: Pacific/Guadalcanal
    +TZGET: Pacific/Guam
    +TZGET: Pacific/Honolulu
    +TZGET: Pacific/Kanton
    +TZGET: Pacific/Kiritimati
    +TZGET: Pacific/Kosrae
    +TZGET: Pacific/Kwajalein
    +TZGET: Pacific/Marquesas
    +TZGET: Pacific/Nauru
    +TZGET: Pacific/Niue
    +TZGET: Pacific/Norfolk
    +TZGET: Pacific/Noumea
    +TZGET: Pacific/Pago_Pago
    +TZGET: Pacific/Palau
    +TZGET: Pacific/Pitcairn
    +TZGET: Pacific/Port_Moresby
    +TZGET: Pacific/Rarotonga
    +TZGET: Pacific/Tahiti
    +TZGET: Pacific/Tarawa
    +TZGET: Pacific/Tongatapu
    +TZGET: UTC
    OK

    AT+DATETIME
    +DATETIME: 2023-10-04 18:38:54
    OK

    AT+AWMMODE
    +AWMMODE: 0
    OK

    AT+AWMSCAN
    +AWMSCAN: 0
    OK

    AT+SISOMODE
    +SISOMODE: 0
    OK

    AT+FIPS
    +FIPS: unsupported
    OK

    AT+LOGDEBUG=0
    +LOGDEBUG: 0
    OK

    AT+LOGDEBUG=1
    +LOGDEBUG: 0
    OK

    AT+FILESLIST
    +FILESLIST: ca.crt
    +FILESLIST: potato.pac
    OK

    AT+WENABLE
    +WENABLE: 1
    OK

    AT+WHARD
    +WHARD: 1
    OK

    AT+WLIST
    +WLIST: Purifiedbagel,74:93:DA:56:64:F5,100,260000,2437,1,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: Purifiedbagel,74:93:DA:56:64:F6,74,540000,5785,1,0,392,9072,WPA2 PSK,wpa-psk
    +WLIST: Spectrum Mobile,56:93:DA:56:64:F6,72,540000,5785,1,0,648,9072,WPA2 802.1X,wpa-eap
    +WLIST: ,BE:D7:D4:68:61:04,55,130000,5785,3,0,392,9072,WPA2 PSK,wpa-psk
    +WLIST: Verizon_S9DRZ6,C8:99:B2:AD:6B:77,45,540000,2412,3,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: SpectrumSetup-97,88:DE:7C:2C:3F:95,47,260000,2437,1,0,392,9065,WPA2 PSK,wpa-psk
    +WLIST: wifi123,74:93:DA:6D:BD:11,49,260000,2437,1,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: 242Irisdale,04:D4:C4:08:66:C0,45,540000,2412,3,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: NETGEAR95,CC:40:D0:00:5B:5C,45,195000,2462,3,0,392,9070,WPA2 PSK,wpa-psk
    +WLIST: MySpectrumWiFif4-2G,A4:08:F5:51:79:FA,45,195000,2462,1,0,392,9070,WPA2 PSK,wpa-psk
    +WLIST: Irisdale_Guest,04:D4:C4:08:66:C1,44,540000,2412,1,0,392,9064,WPA2 PSK,wpa-psk
    +WLIST: rootown,00:06:5A:01:4C:99,44,54000,2462,1,0,648,9065,WPA2 802.1X,wpa-eap
    +WLIST: MojoDojoCasaHouse,F4:05:95:E1:A8:72,37,540000,2412,1,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: DIRECT-6A-HP DeskJet 3630 series,84:A9:3E:C4:0C:6B,35,65000,2437,3,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: Allyn's Boys,90:D0:92:3F:60:6C,32,540000,5805,3,0,33554824,9072,WPA2 PSK,wpa-psk
    +WLIST: Spectrum Mobile,56:37:5F:EE:6E:BE,29,540000,5785,1,0,648,9068,WPA2 802.1X,wpa-eap
    +WLIST: SpectrumSetup-80,2C:EA:DC:CC:45:7E,52,260000,2437,1,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: SpectrumSetup-933D,F0:7B:65:25:93:43,49,540000,2437,1,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: Allyn's Boys,90:D0:92:3F:60:64,42,260000,2457,3,0,33554824,9070,WPA2 PSK,wpa-psk
    +WLIST: AllynsGirls,2C:EA:DC:F2:2E:7F,39,260000,2437,1,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: SpectrumSetup-10,F0:81:75:00:57:16,34,195000,2437,1,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: SpectrumSetup-D80C,F0:7B:65:8D:D8:12,35,540000,2437,1,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: KmacsWifi,A4:97:33:8C:D7:86,25,540000,5785,1,0,392,9068,WPA2 PSK,wpa-psk
    +WLIST: ConnectAkron,00:06:5A:81:4C:99,40,54000,2462,0,0,0,9070,,none
    +WLIST: ,00:06:5A:41:4C:99,44,54000,2462,1,332,0,9070,WPA1 PSK,wpa-psk
    OK

    AT+CONNLIST
    +CONNLIST: e8f008a5-aa29-4038-8484-2c408ccad89e:wfa9,0
    +CONNLIST: aa616959-ba9f-4ad4-bf5e-4eab629c5d58:internal-usb0,1
    +CONNLIST: 8e428f4e-15a3-495c-a3ff-787160394de1:ethernet-eth0,0
    +CONNLIST: 8e428f4e-15a3-495c-a3ff-787160394de2:ethernet-eth1,0
    +CONNLIST: 5ddc1d42-116b-4ac2-b8fa-a744d3692aab:lo,1
    +CONNLIST: ed8927c3-4e8e-4a08-9d46-675549109eae:Purifiedbagel,1
    OK

    AT+NETIF
    +NETIF: lo,eth0,eth1,usb0,wlan0,p2p-dev-wlan0
    OK

# Wifi Commands

### python .\wifi_commands.py
    ATE0
    OK

    AT+WSCAN
    OK

    AT+WLIST
    +WLIST: Purifiedbagel,74:93:DA:56:64:F5,100,260000,2437,1,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: Purifiedbagel,74:93:DA:56:64:F6,74,540000,5785,1,0,392,9072,WPA2 PSK,wpa-psk
    +WLIST: Spectrum Mobile,56:93:DA:56:64:F6,72,540000,5785,1,0,648,9072,WPA2 802.1X,wpa-eap
    +WLIST: ,BE:D7:D4:68:61:04,55,130000,5785,3,0,392,9072,WPA2 PSK,wpa-psk
    +WLIST: Verizon_S9DRZ6,C8:99:B2:AD:6B:77,45,540000,2412,3,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: SpectrumSetup-97,88:DE:7C:2C:3F:95,47,260000,2437,1,0,392,9065,WPA2 PSK,wpa-psk
    +WLIST: wifi123,74:93:DA:6D:BD:11,49,260000,2437,1,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: 242Irisdale,04:D4:C4:08:66:C0,45,540000,2412,3,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: NETGEAR95,CC:40:D0:00:5B:5C,45,195000,2462,3,0,392,9070,WPA2 PSK,wpa-psk
    +WLIST: MySpectrumWiFif4-2G,A4:08:F5:51:79:FA,45,195000,2462,1,0,392,9070,WPA2 PSK,wpa-psk
    +WLIST: Irisdale_Guest,04:D4:C4:08:66:C1,44,540000,2412,1,0,392,9064,WPA2 PSK,wpa-psk
    +WLIST: rootown,00:06:5A:01:4C:99,44,54000,2462,1,0,648,9065,WPA2 802.1X,wpa-eap
    +WLIST: MojoDojoCasaHouse,F4:05:95:E1:A8:72,37,540000,2412,1,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: DIRECT-6A-HP DeskJet 3630 series,84:A9:3E:C4:0C:6B,35,65000,2437,3,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: Allyn's Boys,90:D0:92:3F:60:6C,32,540000,5805,3,0,33554824,9072,WPA2 PSK,wpa-psk
    +WLIST: Spectrum Mobile,56:37:5F:EE:6E:BE,29,540000,5785,1,0,648,9068,WPA2 802.1X,wpa-eap
    +WLIST: SpectrumSetup-80,2C:EA:DC:CC:45:7E,52,260000,2437,1,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: SpectrumSetup-933D,F0:7B:65:25:93:43,49,540000,2437,1,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: Allyn's Boys,90:D0:92:3F:60:64,42,260000,2457,3,0,33554824,9070,WPA2 PSK,wpa-psk
    +WLIST: AllynsGirls,2C:EA:DC:F2:2E:7F,39,260000,2437,1,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: SpectrumSetup-10,F0:81:75:00:57:16,34,195000,2437,1,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: SpectrumSetup-D80C,F0:7B:65:8D:D8:12,35,540000,2437,1,0,392,9069,WPA2 PSK,wpa-psk
    +WLIST: KmacsWifi,A4:97:33:8C:D7:86,25,540000,5785,1,0,392,9068,WPA2 PSK,wpa-psk
    +WLIST: ConnectAkron,00:06:5A:81:4C:99,40,54000,2462,0,0,0,9070,,none
    +WLIST: ,00:06:5A:41:4C:99,44,54000,2462,1,332,0,9070,WPA1 PSK,wpa-psk
    OK

    AT+WHARD
    +WHARD: 1
    OK

    AT+WENABLE=0
    OK

    AT+WENABLE
    +WENABLE: 0
    OK

    AT+WENABLE=1
    OK

    AT+WENABLE
    +WENABLE: 1
    OK

# Connection Commands

### python .\connection_commands.py
    ATE0
    OK

    AT+CONNLIST
    +CONNLIST: aa616959-ba9f-4ad4-bf5e-4eab629c5d58:internal-usb0,1
    +CONNLIST: 8e428f4e-15a3-495c-a3ff-787160394de1:ethernet-eth0,0
    +CONNLIST: 8e428f4e-15a3-495c-a3ff-787160394de2:ethernet-eth1,0
    +CONNLIST: 5ddc1d42-116b-4ac2-b8fa-a744d3692aab:lo,1
    OK

    AT+CONNMOD=0,{"connection":{"autoconnect":0,"id":"{CONNECTION_ID}","interface-name":"wlan0","type":"802-11-wireless","uuid":"","zone": "trusted"},"802-11-wireless":{"mode":"infrastructure","ssid":"CONNECTION_ID"},"802-11-wireless-security":{"key-mgmt":"wpa-psk","psk":"CONNECTION_PASSWORD"}}
    OK

    AT+CONNACT=CONNECTION_ID,1
    OK

    AT+CONNLIST
    +CONNLIST: aa616959-ba9f-4ad4-bf5e-4eab629c5d58:internal-usb0,1
    +CONNLIST: 8e428f4e-15a3-495c-a3ff-787160394de1:ethernet-eth0,0
    +CONNLIST: 8e428f4e-15a3-495c-a3ff-787160394de2:ethernet-eth1,0
    +CONNLIST: 5ddc1d42-116b-4ac2-b8fa-a744d3692aab:lo,1
    +CONNLIST: 0d87f94e-b669-4666-9211-9c2d9a0ebcaf:CONNECTION_ID,1
    OK

    AT+PING=google.com
    +PING: 26.233
    OK

# Siso Mode Commands

### python .\siso_mode_commands.py
    ATE0
    OK

    AT+SISOMODE
    +SISOMODE: 0
    OK

    AT+SISOMODE=1
    OK

    AT+SISOMODE
    +SISOMODE: 1
    OK

    AT+SISOMODE=-1
    OK

# Network Commands

### python .\network_commands.py   
    ATE0
    OK

    AT+NETIF
    +NETIF: lo,eth0,eth1,usb0,wlan0,p2p-dev-wlan0
    OK

    AT+NETIF=wlan0
    +NETIF: {"status":{"state":100,"stateText":"Activated","mtu":1500,"deviceType":2,"deviceTypeText":"Wi-Fi"},"activeConnection":{"id":"CONNECTION_ID","interface-name":"wlan0","permissions":[],"timestamp":1689671565,"type":"802-11-wireless","uuid":"0d87f94e-b669-4666-9211-9c2d9a0ebcaf","zone":"trusted"},"ip4Config":{"addressData":[{"address":"192.168.1.91","prefix":24}],"routeData":[{"dest":"192.168.1.0","prefix":24,"metric":600,"nextHop":""},{"dest":"0.0.0.0","prefix":0,"metric":600,"nextHop":"192.168.1.1"}],"gateway":"192.168.1.1","domains":["lan"],"nameserverData":["192.168.1.1"],"winsServerData":[]},"ip6Config":{"addressData":[{"address":"2603:6010:96f0:a240::176b","prefix":128},{"address":"2603:6010:96f0:a240:b1ca:cae2:2921:a5d0","prefix":64},{"address":"fe80::54ab:2599:a04c:d04d","prefix":64}],"routeData":[{"dest":"fe80::","prefix":64,"metric":1024,"nextHop":""},{"dest":"2603:6010:96f0:a240::","prefix":64,"metric":600,"nextHop":""},{"dest":"2603:6010:96f0:a240::","prefix":60,"metric":600,"nextHop":"fe80::7693:daff:fe56:64f8"},{"dest":"::","prefix":0,"metric":600,"nextHop":"fe80::7693:daff:fe56:64f8"},{"dest":"2603:6010:96f0:a240::176b","prefix":128,"metric":600,"nextHop":""}],"gateway":"fe80::7693:daff:fe56:64f8","domains":[],"nameservers":["2603:6010:96f0:a240::1"]},"dhcp4Config":{"options":{"broadcastAddress":"192.168.1.255","dhcpClientIdentifier":"01:c0:ee:40:43:c4:14","dhcpLeaseTime":"43200","dhcpServerIdentifier":"192.168.1.1","domainName":"lan","domainNameServers":"192.168.1.1","expiry":"1689714763","hostName":"summit","ipAddress":"192.168.1.91","nextServer":"192.168.1.1","requestedBroadcastAddress":"1","requestedDomainName":"1","requestedDomainNameServers":"1","requestedDomainSearch":"1","requestedHostName":"1","requestedInterfaceMtu":"1","requestedMsClasslessStaticRoutes":"1","requestedNisDomain":"1","requestedNisServers":"1","requestedNtpServers":"1","requestedRfc3442ClasslessStaticRoutes":"1","requestedRootPath":"1","requestedRouters":"1","requestedStaticRoutes":"1","requestedSubnetMask":"1","requestedTimeOffset":"1","requestedWpad":"1","routers":"192.168.1.1","subnetMask":"255.255.255.0"}},"dhcp6Config":{"options":{"dhcp6ClientId":"00:04:9f:48:19:bc:e6:84:e3:03:f3:32:86:6e:97:3f:81:bf","dhcp6DomainSearch":"lan","dhcp6NameServers":"2603:6010:96f0:a240::1","fqdnFqdn":"summit","iaid":"d2:59:86:4f","ip6Address":"2603:6010:96f0:a240::176b"}},"wireless":{"bitrate":6000,"permHwAddress":"C0:EE:40:43:C4:14","mode":2,"regDomain":"US","hwAddress":"C0:EE:40:43:C4:14"},"activeAccessPoint":{"ssid":"CONNECTION_ID","hwAddress":"74:93:DA:56:64:F6","maxBitrate":540000,"flags":1,"wpaFlags":0,"rsnFlags":392,"strength":60,"frequency":5785,"signal":-60.0},"udi":"/sys/devices/platform/ahb/ahb:apb/f8000000.mmc/mmc_host/mmc1/mmc1:0001/mmc1:0001:1/net/wlan0","path":"/org/freedesktop/NetworkManager/Devices/10","interface":"wlan0","ipInterface":"wlan0","driver":"lrdmwl_sdio","driverVersion":"6.1.39","firmwareVersion":"N/A","capabilities":1,"stateReason":0,"managed":true,"autoconnect":true,"firmwareMissing":false,"nmPluginMissing":false,"availableConnections":[{"id":"CONNECTION_ID","interface-name":"wlan0","permissions":[],"timestamp":1689671565,"type":"802-11-wireless","uuid":"0d87f94e-b669-4666-9211-9c2d9a0ebcaf","zone":"trusted"}],"physicalPortId":"","metered":4,"meteredText":"Not metered (guessed)","lldpNeighbors":[],"real":true,"ip4Connectivity":4,"ip4ConnectivityText":"Full","ip6Connectivity":4,"ip6ConnectivityText":"Full","interfaceFlags":65539}
    OK

    AT+NETIFSTAT=wlan0
    +NETIFSTAT: 80641,445,0,0,0,21205,169,0,0
    OK

    AT+NETIFVIRT=1
    OK

    AT+NETIF
    +NETIF: lo,eth0,eth1,usb0,wlan0,p2p-dev-wlan0,wlan1,p2p-dev-wlan1
    OK

    AT+NETIFVIRT=0
    OK

# Log Commands

### python .\log_commands.py  
    ATE0
    OK

    AT+LOGFWD=1
    ERROR
    AT+LOGFWD=0
    OK

    AT+LOGDEBUG=0
    +LOGDEBUG: 0
    OK

    AT+LOGDEBUG=0,5
    OK

    AT+LOGDEBUG=0
    +LOGDEBUG: 5
    OK

    AT+LOGDEBUG=0,0
    OK

    AT+LOGDEBUG=1
    +LOGDEBUG: 0
    OK

    AT+LOGDEBUG=1,1
    OK

    AT+LOGDEBUG=1
    +LOGDEBUG: 1
    OK

    AT+LOGDEBUG=1,0
    OK

    AT+LOGGET=0,7,1
    ...
    +LOGGET: {'time': '2023-07-18 09:12:34.624075', 'priority': '6', 'identifier': 'kernel', 'message': 'ieee80211 phy2: WMM Turbo=1'}
    +LOGGET: {'time': '2023-07-18 09:12:35.464153', 'priority': '6', 'identifier': 'kernel', 'message': 'atmel_usart_serial atmel_usart_serial.0.auto: using dma0chan6 for rx DMA transfers'}
    +LOGGET: {'time': '2023-07-18 09:12:35.495144', 'priority': '6', 'identifier': 'kernel', 'message': 'atmel_usart_serial atmel_usart_serial.0.auto: using dma0chan7 for tx DMA transfers'}
    +LOGGET: {'time': '2023-07-18 09:12:35.624110', 'priority': '6', 'identifier': 'kernel', 'message': 'Bluetooth: MGMT ver 1.22'}
    +LOGGET: {'time': '2023-07-18 09:12:40.644028', 'priority': '6', 'identifier': 'kernel', 'message': 'wlan0: authenticate with 74:93:da:56:64:f6'}
    +LOGGET: {'time': '2023-07-18 09:12:40.654081', 'priority': '6', 'identifier': 'kernel', 'message': 'wlan0: send auth to 74:93:da:56:64:f6 (try 1/3)'}
    +LOGGET: {'time': '2023-07-18 09:12:40.674524', 'priority': '6', 'identifier': 'kernel', 'message': 'wlan0: authenticated'}
    +LOGGET: {'time': '2023-07-18 09:12:40.675482', 'priority': '6', 'identifier': 'kernel', 'message': 'wlan0: associate with 74:93:da:56:64:f6 (try 1/3)'}
    +LOGGET: {'time': '2023-07-18 09:12:40.686118', 'priority': '6', 'identifier': 'kernel', 'message': 'wlan0: RX AssocResp from 74:93:da:56:64:f6 (capab=0x1511 status=0 aid=11)'}
    +LOGGET: {'time': '2023-07-18 09:12:40.704135', 'priority': '6', 'identifier': 'kernel', 'message': 'wlan0: associated'}
    +LOGGET: {'time': '2023-07-18 09:12:40.814742', 'priority': '6', 'identifier': 'kernel', 'message': 'IPv6: ADDRCONF(NETDEV_CHANGE): wlan0: link becomes ready'}
    OK

# HTTP Commands

### python .\http_commands.py  
    ATE0
    OK

    AT+HTTPCONF=www.google.com,80,1,/
    OK

    AT+HTTPRSHDR=1
    +HTTPRSHDR: 1
    OK

    AT+HTTPADDHDR=foo,bar
    OK

    AT+HTTPEXE=11
    >
    Hello World
    +HTTPEXE: Content-Type:text/html; charset=UTF-8,Referrer-Policy:no-referrer,Content-Length:1555,Date:Wed, 04 Oct 2023 18:55:37 GMT,Content-Type:text/html; charset=UTF-8,Referrer-Policy:no-referrer,Content-Length:1555,Date:Wed, 04 Oct 2023 18:55:37 GMT
    <!DOCTYPE html>
    <html lang=en>
    <meta charset=utf-8>
    <meta name=viewport content="initial-scale=1, minimum-scale=1, width=device-width">
    <title>Error 400 (Bad Request)!!1</title>
    <style>
        *{margin:0;padding:0}html,code{font:15px/22px arial,sans-serif}html{background:#fff;color:#222;padding:15px}body{margin:7% auto 0;max-width:390px;min-height:180px;padding:30px 0 15px}* > body{background:url(//www.google.com/images/errors/robot.png) 100% 5px no-repeat;padding-right:205px}p{margin:11px 0 22px;overflow:hidden}ins{color:#777;text-decoration:none}a img{border:0}@media screen and (max-width:772px){body{background:none;margin-top:0;max-width:none;padding-right:0}}#logo{background:url(//www.google.com/images/branding/googlelogo/1x/googlelogo_color_150x54dp.png) no-repeat;margin-left:-5px}@media only screen and (min-resolution:192dpi){#logo{background:url(//www.google.com/images/branding/googlelogo/2x/googlelogo_color_150x54dp.png) no-repeat 0% 0%/100% 100%;-moz-border-image:url(//www.google.com/images/branding/googlelogo/2x/googlelogo_color_150x54dp.png) 0}}@media only screen and (-webkit-min-device-pixel-ratio:2){#logo{background:url(//www.google.com/images/branding/googlelogo/2x/googlelogo_color_150x54dp.png) no-repeat;-webkit-background-size:100% 100%}}#logo{display:inline-block;height:54px;width:150px}
    </style>
    <a href=//www.google.com/><span id=logo aria-label=Google></span></a>
    <p><b>400.</b> <ins>That’s an error.</ins>
    <p>Your client has issued a malformed or illegal request.  <ins>That’s all we know.</ins>

    OK

# Files Commands

### python .\files_commands.py  
    ATE0
    OK

    AT+FILESLIST
    +FILESLIST: ca.crt
    +FILESLIST: potato.pac
    OK

    AT+CERTGET=ca.crt
    +CERTGET: {"version":1,"serial_number":"92926636221347987888259568196595107023764099625","subject":"/C=US/ST=OH/L=Akron/O=LairdConnectivity/OU=IT/CN=www.lairdconnect.com/emailAddress=info@lairdconnect.com","issuer":"/C=US/ST=OH/L=Akron/O=LairdConnectivity/OU=IT/CN=www.lairdconnect.com/emailAddress=info@lairdconnect.com","not_before":"Feb 18 13:28:23 2021 GMT","not_after":"Feb 16 13:28:23 2031 GMT","extensions":[]}
    OK

    AT+FILESUP=0,11,potato.crt
    >
    Hello World
    OK

    AT+FILESUP=0,11,potato.pac
    >
    Hello World
    OK

    AT+FILESLIST
    +FILESLIST: ca.crt
    +FILESLIST: potato.crt
    +FILESLIST: potato.pac
    OK

    AT+FILESDEL=potato.crt
    OK

    AT+FILESLIST
    +FILESLIST: ca.crt
    +FILESLIST: potato.pac
    OK

    AT+FILESEXP=0,3,summit
    +FILESEXP: 2785
    OK

    AT+FILESEXP=1,3,1000,0
    b'\r\n+FILESEXP: 1000,PK\x03\x04\n\x00\x00\x00\x00\x00\x85I\xf2V\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00&\x00\x1c\x00etc/NetworkManager/system-connections/UT\t\x00\x03iW\xb6d\xeb\xc3\x1aeux\x0b\x00\x01\x04\x00\x00\x00\x00\x04\x00\x00\x00\x00PK\x03\x04\x14\x00\x0b\x00\x08\x00\x85I\xf2V\xf8\'\x7f\x07\xde\x00\x00\x003\x01\x00\x00@\x00\x1c\x00etc/NetworkManager/system-connections/Purifiedbagel.nmconnectionUT\t\x00\x03iW\xb6diW\xb6dux\x0b\x00\x01\x04\x00\x00\x00\x00\x04\x00\x00\x00\x00~\x98\xe1~\xfe6\x15\x8d\x10\xe6n\x84\x18\x12\xe95\x02kue\xa1]S\x84mAw\x91\x0fA\xec\x1b\x8d{\x88\xb3\x1b.\x0f"\xa3)\x01\xdb*\x93\xb3\xa5o3\xf1G\x8ep}\x8a\xdbI\x8f\xedJ\\\xa6?2\xf9\x8fn\x92\xe3\xcb\xddx\xabyC\x96\x90l\xfb\xe0\x13\xae\x97\xe8\xa4.!}\x92\xaag\x04\xe4M\xcfPd\xdb;E\xa0[i\xe5X\xbcZ\x14\t\x810\xd3\xce\x82\x0c\x81>\xe2\xcb>\x96\xd7\\\xfe*\x03t\xec\xe9*w\x06#\xd4h\xa6\xbf11\xc8\xe2\xcc$\x16\x8b\xaaU\x82\xe9\xdf\x96\xe5\x9c\xdf\xe4\xb7\x915\xae+\xeb\xb1#@\x8a\xc4\x86k\xed.R\xe4\x92\x07DY\r\x01\x1e\xb1\xa9\xbb\x133\xcb\xfd\xc5\x87/\xcf\x92\xd1%\x9a\xb8\xe2{7\xca\x99\xbf\xeeIqe \xa2d\x9a\xf3U.\xbf\xc9\xcd\xcd,\xb3\xe5\xaf\xd9PK\x07\x08\xf8\'\x7f\x07\xde\x00\x00\x003\x01\x00\x00PK\x03\x04\x14\x00\x0b\x00\x08\x00\x0c\x869W\xc5(\xf3b\xd3\x00\x00\x00\x1c\x01\x00\x007\x00\x1c\x00etc/NetworkManager/system-connections/wfa9.nmconnectionUT\t\x00\x03\xd8\xb9\x11e\xd8\xb9\x11eux\x0b\x00\x01\x04\x00\x00\x00\x00\x04\x00\x00\x00\x00\xb7\x8d\xc4\xca\xc0\n\xba2\xa7\xff\xb9n\t\xa0\xf5YK>>J\x0bTO d\x18\xc1p\x90>\n7\xfa6\xad\x96#\xe9\xd3\xf0\xdd,\nc\x9d~\xe3t[@&\xac\xab\x84\x92\xb1\xff\xaa\xcc=\x18\x9fZy\x12#Q\xee=\xd98\xd1\x96\x7f$\xb9CFO<q-\x90\xc0"|U\xde\xe8\xed\x15\xb0\xc7h\xc1\xbf\x17\xda\xa3#\x9f\x1a\x83\x95\xff\xc0\xd1/6\x96\x945V\xc1\xe7\x8d\xe9e\xa9\xb5x\x1d\r\xf8\x11\xb5\xe7b\xa5\xde\xfb\x94\x0c\xb3\x18O\x83\\\xbc1\xd1\xba\xb4\xfeq\xd2\xe4\xa3\x90w`\xf6)\x9e}O \x8f\xabh\x18\xfb\xd9Q\x0c\x04\x8a\xefG\xf3\xdc\xa7M\xe2s~\xb5\xf06\xdc\x15\xc5\x8fQ\xe9,kf\xe7\x08\x90{\xda\x0f\xbe\x9c\xc7\x8e\x1f\x1dY\xb7\xadtz\xfe,tNL\xedPK\x07\x08\xc5(\xf3b\xd3\x00\x00\x00\x1c\x01\x00\x00PK\x03\x04\n\x00\x00\x00\x00\x00\xc1J\xf2V\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x19\x00\x1c\x00etc/NetworkManager/certs/UT\t\x00\x03\xbaY\xb6d\xeb\xc3\x1aeux\x0b\x00\x01\x04\x00\x00\x00\x00\x04\x00\x00\x00\x00PK\x03\x04\n\x00\x0b\x00\x00\x00\xc1J\xf2VV\xb1\x17J\x17\x00\x00\x00\x0b\x00\x00\x00#\x00\x1c\x00etc/NetworkManager/certs/potato.pacUT\t\x00\x03\xbaY\xb6dw\x02\x1beux\x0b\x00\x01\x04\x00\x00\x00\x00\x04\x00\x00\x00\x00\xf4\xaa\x8b\xa8\xc7\xf6\x80n\x8a\xd4L\xa56\x90\xdb\xee\xca\xeff\xa0\xc4\xee\xffPK\x07\x08V'
    OK

# Datetime Commands

### python .\datetime_commands.py  
    ATE0
    OK

    AT+DATETIME
    +DATETIME: 2023-07-18 09:22:54
    OK

    AT+DATETIME=1999999999999999
    OK

    AT+DATETIME
    +DATETIME: 2033-05-18 03:33:20
    OK

    AT+DATETIME=1695659975000000
    OK

    AT+NTPGET
    +NTPGET: time.nist.gov,static
    OK

    AT+NTPCONF=0,pool.ntp.org
    OK

    AT+NTPGET
    +NTPGET: time.nist.gov,static
    +NTPGET: pool.ntp.org,static
    OK

    AT+NTPCONF=1,pool.ntp.org
    OK

    AT+TZGET
    +TZGET: Etc/UTC
    OK

    AT+TZSET=Pacific/Tahiti
    OK

    AT+TZGET
    +TZGET: Pacific/Tahiti
    OK

    AT+TZSET=Etc/UTC
    OK

# CIP Commands

### python .\cip_commands.py 
    ATE0
    OK

    AT+PING=google.com
    +PING: 27.692
    OK

    AT+CIPSTART=0,0,google.com,80
    OK

    AT+CIPSEND=0,11
    +IP: 0,Connected
    >
    Hello World
    OK

    AT+CIPCLOSE=0
    +IP: 0,Disconnected
    OK

# AWM Commands

### python .\awm_commands.py  
    ATE0
    OK

    AT+AWMMODE
    +AWMMODE: 0
    OK

    AT+AWMSCAN
    +AWMSCAN: 0
    OK

    AT+AWMSCAN=1
    OK

    AT+AWMSCAN
    +AWMSCAN: 1
    OK

    AT+AWMSCAN=0
    OK

# Reboot command

### python .\reboot_command.py  
    AT+POWER=3
    OK

    AT
    OK

# Firmware Update Commands

### python .\firmware_update_commands.py  
    ATE0
    OK

    AT+FWRUN=1,2
    OK

    AT+FWSTATUS
    +FWSTATUS: 5
    OK

    AT+FWSEND=48440832
    >

    +FWSEND: 48440832
    OK

    AT+POWER=3
    +FWSEND: 48440832
    OK

    OK

    AT
    OK

# Fips Commands
### python .\fips_commands.py  
    ATE0
    OK

    AT+FIPS
    +FIPS: unset
    OK

    AT+FIPS=1,1
    OK

    AT+FIPS
    +FIPS: fips_wifi
    OK
# Factory Reset Command

### python .\factory_reset_command.py 
    AT+FACTRESET=1
    +FACTRESET: 0
    OK

    AT
    OK