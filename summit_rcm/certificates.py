import os
from syslog import LOG_ERR, syslog
from typing import Optional, Tuple
import falcon
from .files import FilesManage
from . import definition

import openssl_extension


class Certificates:
    """
    Certificate management
    """

    @classmethod
    def get_cert_info(
        self, cert_name: str, password: Optional[str] = None
    ) -> Tuple[dict, str]:
        """
        Retrieve the basic meta data info about the given certificate name from the certificates
        managed by Summit RCM/NetworkManager.

        Return value is a tuple in the form (cert_info, info_msg)
        """

        cert_file_path = "{0}/{1}".format(
            str(definition.FILEDIR_DICT.get("cert")), cert_name
        )

        if not os.path.exists(cert_file_path):
            return ({}, f"Cannot find certificate with name {cert_name}")

        try:
            cert_info = openssl_extension.get_cert_info(cert_file_path, password)
            return (cert_info, "")
        except Exception as e:
            error_msg = f"{str(e)}"
            syslog(LOG_ERR, error_msg)
            return ({}, error_msg)

    async def on_get(self, req, resp):
        """
        Retrieve either a list of all certificates or info on just one if the name parameter is
        provided
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "",
        }

        cert_name = req.params.get("name", None)
        password = req.params.get("password", None)
        try:
            if cert_name:
                (cert_info, info_msg) = self.get_cert_info(
                    cert_name, password if password else None
                )
                result["cert_info"] = cert_info
                result["InfoMsg"] = info_msg
                if len(cert_info) > 0:
                    result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            else:
                # No cert name give, so just return the list of certs available
                files = FilesManage.get_cert_or_pac_files("cert")
                result["files"] = files
                result["count"] = len(files)
                result["InfoMsg"] = "cert files"
                result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as e:
            syslog(LOG_ERR, f"Could not read certificate info: {str(e)}")
            result["InfoMsg"] = "Could not read certificate info"

        resp.media = result
