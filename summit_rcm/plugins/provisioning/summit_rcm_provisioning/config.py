#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2026 Ezurio LLC.
#
"""Configuration parser for the certificate provisioning plugin"""

import configparser
from typing import Optional

from summit_rcm import definition


class ProvisioningConfig:
    """
    Parser for the provisioning filesystem paths defined in the server config
    file (e.g. /etc/summit-rcm.ini). The paths are written into the config by
    the build system so the plugin resolves them itself instead of
    relying on the core ServerConfig.
    """

    def __init__(self, config_file: Optional[str] = None):
        self.parser = configparser.ConfigParser(interpolation=None)
        try:
            self.parser.read(
                definition.resolve_ini_files(
                    config_file or definition.SUMMIT_RCM_SERVER_CONF_FILE
                )
            )
        except Exception:
            self.parser = configparser.ConfigParser(interpolation=None)

    def get(self, section: str, key: str, fallback: str) -> str:
        """Get a raw value from the server config"""
        return self.parser.get(section=section, option=key, fallback=fallback).strip(
            '"'
        )

    @property
    def data_dir(self) -> str:
        """Runtime data directory (from the [summit-rcm] ini section)"""
        return self.get("summit-rcm", "data_dir", definition.SUMMIT_RCM_DATA_DIR)

    @property
    def provisioning_dir(self) -> str:
        """Provisioning directory (from the [summit-rcm] ini section)"""
        return self.get("summit-rcm", "provisioning_dir", definition.PROVISIONING_DIR)

    @property
    def ssl_private_key(self) -> str:
        """Provisioning SSL private key (from the [summit-rcm] ini section)"""
        return self.get(
            "summit-rcm",
            "provisioning_ssl_private_key",
            definition.PROVISIONING_SERVER_KEY_PATH,
        )

    @property
    def ssl_certificate(self) -> str:
        """Provisioning SSL certificate (from the [summit-rcm] ini section)"""
        return self.get(
            "summit-rcm",
            "provisioning_ssl_certificate",
            definition.PROVISIONING_SERVER_CERT_PATH,
        )

    @property
    def ssl_certificate_chain(self) -> str:
        """Provisioning SSL CA chain (from the [summit-rcm] ini section)"""
        return self.get(
            "summit-rcm",
            "provisioning_ssl_certificate_chain",
            definition.PROVISIONING_CA_CERT_CHAIN_PATH,
        )

    @property
    def server_ssl_private_key(self) -> str:
        """Server SSL private key (from the [global] ini section)"""
        return self.get(
            "global",
            "server.ssl_private_key",
            f"{self.data_dir}/ssl/server.key",
        )

    @property
    def server_ssl_certificate(self) -> str:
        """Server SSL certificate (from the [global] ini section)"""
        return self.get(
            "global",
            "server.ssl_certificate",
            f"{self.data_dir}/ssl/server.crt",
        )

    @property
    def server_ssl_certificate_chain(self) -> str:
        """
        Server SSL CA chain (from the [global] ini section), falling back to the
        provisioning CA chain
        """
        return self.get(
            "global",
            "server.ssl_certificate_chain",
            self.ssl_certificate_chain,
        )

    @property
    def device_server_key_path(self) -> str:
        """Path of the provisioned device private key"""
        return self.get(
            "summit-rcm",
            "device_server_key",
            f"{self.provisioning_dir}/dev.key",
        )

    @property
    def device_server_csr_path(self) -> str:
        """Path of the provisioned device certificate signing request"""
        return self.get(
            "summit-rcm",
            "device_server_csr",
            f"{self.provisioning_dir}/dev.csr",
        )

    @property
    def device_server_cert_path(self) -> str:
        """Path of the provisioned device server certificate"""
        return self.get(
            "summit-rcm",
            "device_server_cert",
            f"{self.provisioning_dir}/dev.crt",
        )

    @property
    def provisioning_state_file_path(self) -> str:
        """Path of the provisioning state file"""
        return f"{self.provisioning_dir}/state"
