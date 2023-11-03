"""
Module to interact with network connection profiles
"""

import os
from syslog import LOG_ERR, syslog
import falcon.asgi.multipart
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.rest_api.services.rest_files_service import (
    RESTFilesService as FilesService,
)
from summit_rcm.services.network_service import (
    ConnectionProfileAlreadyActiveError,
    ConnectionProfileAlreadyInactiveError,
    ConnectionProfileNotFoundError,
    ConnectionProfileReservedError,
    NetworkService,
)

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        BadRequestErrorResponseModel,
        ConnectionProfile,
        ConnectionProfileExportRequestModel,
        ConnectionProfileImportRequestFormModel,
        ConnectionProfiles,
        InternalServerErrorResponseModel,
        NotFoundErrorResponseModel,
        UnauthorizedErrorResponseModel,
    )
    from summit_rcm.rest_api.utils.spectree.tags import network_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    BadRequestErrorResponseModel = None
    ConnectionProfile = None
    ConnectionProfileExportRequestModel = None
    ConnectionProfileImportRequestFormModel = None
    ConnectionProfiles = None
    InternalServerErrorResponseModel = None
    NotFoundErrorResponseModel = None
    UnauthorizedErrorResponseModel = None
    network_tag = None


spec = SpectreeService()


class NetworkConnectionsResource(object):
    """
    Resource to handle queries and requests for all network connection profiles
    """

    @spec.validate(
        resp=Response(
            HTTP_200=ConnectionProfiles,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        Retrieve a list of connection profiles
        """
        try:
            resp.media = await NetworkService.get_all_connection_profiles(
                is_legacy=False
            )
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to retrieve list of network connection profiles: {str(exception)}",
            )
            resp.status = falcon.HTTP_500

    @spec.validate(
        json=ConnectionProfile,
        resp=Response(
            HTTP_200=ConnectionProfile,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_post(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        Add a new connection profile
        """
        try:
            post_data: dict = await req.get_media()
            connection_settings = post_data.get("connection", None)
            if not connection_settings:
                resp.status = falcon.HTTP_400
                return

            if connection_settings.get("uuid", None):
                # This should be done with a PUT request
                resp.status = falcon.HTTP_400
                return

            connection_settings_id = connection_settings.get("id", None)
            if (
                connection_settings_id
                and await NetworkService.connection_profile_exists_by_id(
                    id=connection_settings_id
                )
            ):
                # A connection profile with the requested name (id) already exists
                resp.status = falcon.HTTP_400
                return

            resp.media = await NetworkService.create_connection_profile(
                settings=post_data, overwrite_existing=True, is_legacy=False
            )
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_201
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to create network connection: {str(exception)}",
            )
            resp.status = falcon.HTTP_500


class NetworkConnectionsExportResource:
    """
    Resource to handle queries and requests for exporting network connections
    """

    @spec.validate(
        json=ConnectionProfileExportRequestModel,
        resp=Response(
            HTTP_200=None,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_get(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        Retrieve a password-protected archive export of the current connection profiles
        """
        archive = ""
        try:
            get_data = await req.get_media()
            password = get_data.get("password", "")
            if not password:
                resp.status = falcon.HTTP_400
                return

            success, msg, archive = FilesService.export_connections(password)
            if not success:
                raise Exception(msg)

            resp.stream = await FilesService.handle_file_download(archive)
            resp.content_type = falcon.MEDIA_TEXT
            resp.status = falcon.HTTP_200
        except Exception as exception:
            syslog(f"Could not export connections - {str(exception)}")
            resp.status = falcon.HTTP_500
        finally:
            if os.path.isfile(archive):
                os.unlink(archive)


class NetworkConnectionsImportResource:
    """
    Resource to handle queries and requests for importing network connections
    """

    @spec.validate(
        form=ConnectionProfileImportRequestFormModel,
        resp=Response(
            HTTP_200=None,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        Import a password-protected archive of connection profiles
        """
        try:
            password = ""
            overwrite_existing = False

            form = await req.get_media()
            if not isinstance(form, falcon.asgi.multipart.MultipartForm):
                resp.status = falcon.HTTP_400
                return

            async for part in form:
                if part.name == "archive":
                    if not await FilesService.handle_connection_import_file_upload_multipart_form(
                        part
                    ):
                        raise Exception("error uploading file")
                elif part.name == "config":
                    if part.content_type != falcon.MEDIA_JSON:
                        resp.status = falcon.HTTP_400
                        return
                    part_data = await part.get_media()
                    password = part_data.get("password", "")
                    overwrite_existing = part_data.get("overwrite", False)

            if not password:
                resp.status = falcon.HTTP_400
                return

            success, msg = await FilesService.import_connections(
                password, overwrite_existing
            )
            if not success:
                raise Exception(msg)
            resp.status = falcon.HTTP_200
        except Exception as exception:
            syslog(f"Could not import connections - {str(exception)}")
            resp.status = falcon.HTTP_500


class NetworkConnectionResourceByUuid(object):
    """
    Resource to handle queries and requests for a specific network connection profile by UUID
    """

    @spec.validate(
        resp=Response(
            HTTP_200=ConnectionProfile,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_get(
        self, _: falcon.asgi.Request, resp: falcon.asgi.Response, uuid: str
    ) -> None:
        """
        Retrieve details about a connection profile by UUID
        """
        try:
            if not uuid:
                resp.status = falcon.HTTP_400
                return

            resp.media = await NetworkService.get_connection_profile_settings(
                uuid=uuid, id=None, extended=True, is_legacy=False
            )
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except ConnectionProfileNotFoundError:
            resp.status = falcon.HTTP_404
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to retrieve network connection: {str(exception)}",
            )
            resp.status = falcon.HTTP_500

    @spec.validate(
        json=ConnectionProfile,
        resp=Response(
            HTTP_200=ConnectionProfile,
            HTTP_201=ConnectionProfile,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response, uuid: str
    ) -> None:
        """
        Create/replace a connection profile by UUID
        """
        try:
            if not uuid:
                resp.status = falcon.HTTP_400
                return

            put_data: dict = await req.get_media()
            connection_settings = put_data.get("connection", None)
            if not connection_settings:
                resp.status = falcon.HTTP_400
                return

            connection_settings_uuid = connection_settings.get("uuid", None)
            if connection_settings_uuid is None:
                put_data["connection"]["uuid"] = uuid
            elif connection_settings_uuid != uuid:
                resp.status = falcon.HTTP_400
                return

            if await NetworkService.connection_profile_exists_by_uuid(uuid=uuid):
                # The specified connection profile exists, so update it with the provided settings
                resp.media = await NetworkService.update_connection_profile(
                    new_settings=put_data, uuid=uuid, id=None, is_legacy=False
                )
                resp.status = falcon.HTTP_200
            else:
                # The specified connection profile does not exist, so create a new one
                resp.media = await NetworkService.create_connection_profile(
                    settings=put_data, overwrite_existing=True, is_legacy=False
                )
                resp.status = falcon.HTTP_201
            resp.content_type = falcon.MEDIA_JSON
        except ConnectionProfileNotFoundError:
            resp.status = falcon.HTTP_404
        except ConnectionProfileReservedError:
            resp.status = falcon.HTTP_400
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to create/replace network connection: {str(exception)}",
            )
            resp.status = falcon.HTTP_500

    @spec.validate(
        json=ConnectionProfile,
        resp=Response(
            HTTP_200=ConnectionProfile,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_patch(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response, uuid: str
    ) -> None:
        """
        Update/activate/deactivate a connection profile by UUID
        """
        try:
            if not uuid:
                resp.status = falcon.HTTP_400
                return

            patch_data: dict = await req.get_media()
            connection_settings = patch_data.get("connection", None)

            connection_settings_uuid = (
                connection_settings.get("uuid", None)
                if connection_settings is not None
                else None
            )
            if connection_settings_uuid and connection_settings_uuid != uuid:
                resp.status = falcon.HTTP_400
                return

            resp.media = await NetworkService.update_connection_profile(
                new_settings=patch_data, uuid=uuid, id=None, is_legacy=False
            )
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except ConnectionProfileNotFoundError:
            resp.status = falcon.HTTP_404
        except (
            ConnectionProfileAlreadyActiveError,
            ConnectionProfileAlreadyInactiveError,
            ConnectionProfileReservedError,
        ):
            resp.status = falcon.HTTP_400
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to update network connection: {str(exception)}",
            )
            resp.status = falcon.HTTP_500

    @spec.validate(
        resp=Response(
            HTTP_200=None,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_delete(
        self, _: falcon.asgi.Request, resp: falcon.asgi.Response, uuid: str
    ) -> None:
        """
        Remove a connection profile by UUID
        """
        try:
            if not uuid:
                resp.status = falcon.HTTP_400
                return

            await NetworkService.delete_connection_profile(uuid=uuid, id=None)
            resp.status = falcon.HTTP_200
        except ConnectionProfileNotFoundError:
            resp.status = falcon.HTTP_404
        except ConnectionProfileReservedError:
            resp.status = falcon.HTTP_400
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to remove network connection: {str(exception)}",
            )
            resp.status = falcon.HTTP_500


class NetworkConnectionResourceById(object):
    """
    Resource to handle queries and requests for a specific network connection profile by id
    """

    @spec.validate(
        resp=Response(
            HTTP_200=ConnectionProfile,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_get(
        self, _: falcon.asgi.Request, resp: falcon.asgi.Response, id: str
    ) -> None:
        """
        Retrieve details about a connection profile by id (name)
        """
        try:
            if not id:
                resp.status = falcon.HTTP_400
                return

            resp.media = await NetworkService.get_connection_profile_settings(
                uuid=None, id=id, extended=True, is_legacy=False
            )
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except ConnectionProfileNotFoundError:
            resp.status = falcon.HTTP_404
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to retrieve network connection: {str(exception)}",
            )
            resp.status = falcon.HTTP_500

    @spec.validate(
        json=ConnectionProfile,
        resp=Response(
            HTTP_200=ConnectionProfile,
            HTTP_201=ConnectionProfile,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response, id: str
    ) -> None:
        """
        Create/replace a connection profile by id (name)
        """
        try:
            if not id:
                resp.status = falcon.HTTP_400
                return

            put_data: dict = await req.get_media()
            connection_settings = put_data.get("connection", None)
            if not connection_settings:
                resp.status = falcon.HTTP_400
                return

            connection_settings_id = connection_settings.get("id", None)
            if connection_settings_id is None:
                put_data["connection"]["id"] = id
            elif (
                connection_settings_id != id
                and await NetworkService.connection_profile_exists_by_id(
                    id=connection_settings_id
                )
            ):
                # A connection profile with the requested name (id) already exists
                resp.status = falcon.HTTP_400
                return

            if await NetworkService.connection_profile_exists_by_id(id=id):
                # The specified connection profile exists, so update it with the provided settings
                resp.media = await NetworkService.update_connection_profile(
                    new_settings=put_data, uuid=None, id=id, is_legacy=False
                )
                resp.status = falcon.HTTP_200
            else:
                # The specified connection profile does not exist, so try to create a new one

                if connection_settings_id and connection_settings_id != id:
                    # If a connection profile with an id of 'id' doesn't exist, but the 'id' in the
                    # PUT data JSON body doesn't match it, this is a bad request.
                    resp.status = falcon.HTTP_400
                    return

                resp.media = await NetworkService.create_connection_profile(
                    settings=put_data, overwrite_existing=True, is_legacy=False
                )
                resp.status = falcon.HTTP_201
            resp.content_type = falcon.MEDIA_JSON
        except ConnectionProfileNotFoundError:
            resp.status = falcon.HTTP_404
        except ConnectionProfileReservedError:
            resp.status = falcon.HTTP_400
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to create/replace network connection: {str(exception)}",
            )
            resp.status = falcon.HTTP_500

    @spec.validate(
        json=ConnectionProfile,
        resp=Response(
            HTTP_200=ConnectionProfile,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_patch(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response, id: str
    ) -> None:
        """
        Update/activate/deactivate a connection profile by id (name)
        """
        try:
            if not id:
                resp.status = falcon.HTTP_400
                return

            patch_data: dict = await req.get_media()
            connection_settings = patch_data.get("connection", None)

            connection_settings_id = (
                connection_settings.get("id", None)
                if connection_settings is not None
                else None
            )
            if (
                connection_settings_id
                and connection_settings_id != id
                and await NetworkService.connection_profile_exists_by_id(
                    id=connection_settings_id
                )
            ):
                # A connection profile with the requested name (id) already exists
                resp.status = falcon.HTTP_400
                return

            resp.media = await NetworkService.update_connection_profile(
                new_settings=patch_data, uuid=None, id=id, is_legacy=False
            )
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except ConnectionProfileNotFoundError:
            resp.status = falcon.HTTP_404
        except (
            ConnectionProfileAlreadyActiveError,
            ConnectionProfileAlreadyInactiveError,
            ConnectionProfileReservedError,
        ):
            resp.status = falcon.HTTP_400
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to update network connection: {str(exception)}",
            )
            resp.status = falcon.HTTP_500

    @spec.validate(
        resp=Response(
            HTTP_200=None,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_delete(
        self, _: falcon.asgi.Request, resp: falcon.asgi.Response, id: str
    ) -> None:
        """
        Remove a connection profile by id (name)
        """
        try:
            if not id:
                resp.status = falcon.HTTP_400
                return

            await NetworkService.delete_connection_profile(uuid=None, id=id)
            resp.status = falcon.HTTP_200
        except ConnectionProfileNotFoundError:
            resp.status = falcon.HTTP_404
        except ConnectionProfileReservedError:
            resp.status = falcon.HTTP_400
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to remove network connection: {str(exception)}",
            )
            resp.status = falcon.HTTP_500
