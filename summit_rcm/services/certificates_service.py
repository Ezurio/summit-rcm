"""
Module to interact with the certificates.
"""

import os
from syslog import syslog, LOG_ERR
from typing import Optional, Tuple

try:
    import openssl_extension
except ImportError as error:
    # Ignore the error if the openssl_extension module is not available if generating documentation
    if os.environ.get("DOCS_GENERATION") != "True":
        raise error
from summit_rcm import definition


class CertificatesService:
    """Service to interact with the certificates."""

    @staticmethod
    def get_cert_info(
        cert_name: str, password: Optional[str] = None
    ) -> Tuple[dict, str]:
        """
        Retrieve the basic meta data info about the given certificate name from the certificates
        managed by Summit RCM/NetworkManager.

        Return value is a tuple in the form (cert_info, info_msg)
        """

        cert_file_path = f"{str(definition.FILEDIR_DICT.get('cert'))}/{cert_name}"

        if not os.path.exists(cert_file_path):
            return ({}, f"Cannot find certificate with name {cert_name}")

        try:
            cert_info = openssl_extension.get_cert_info(cert_file_path, password)
            return (cert_info, "")
        except Exception as exception:
            error_msg = f"{str(exception)}"
            syslog(LOG_ERR, error_msg)
            return ({}, error_msg)
