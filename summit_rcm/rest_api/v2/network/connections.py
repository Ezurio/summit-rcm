"""
Module to interact with network connection profiles
"""

import os
from syslog import LOG_ERR, syslog
import falcon.asgi.multipart
from summit_rcm.services.files_service import FilesService
from summit_rcm.services.network_service import (
    ConnectionProfileAlreadyActiveError,
    ConnectionProfileAlreadyInactiveError,
    ConnectionProfileNotFoundError,
    ConnectionProfileReservedError,
    NetworkService,
)


class NetworkConnectionsResource(object):
    """
    Resource to handle queries and requests for all network connection profiles
    """

    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        GET handler for the /network/connections endpoint
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

    async def on_post(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        POST handler for the /network/connections endpoint
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

    async def on_get(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        GET handler for the /network/connections/export endpoint
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

    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        PUT handler for the /network/connections/import endpoint
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
                    if not await FilesService.handle_connection_import_file_upload(
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

    async def on_get(
        self, _: falcon.asgi.Request, resp: falcon.asgi.Response, uuid: str
    ) -> None:
        """
        GET handler for the /network/connections/uuid/{uuid} endpoint
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

    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response, uuid: str
    ) -> None:
        """
        PUT handler for the /network/connections/uuid/{uuid} endpoint
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

    async def on_patch(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response, uuid: str
    ) -> None:
        """
        PATCH handler for the /network/connections/uuid/{uuid} endpoint
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

    async def on_delete(
        self, _: falcon.asgi.Request, resp: falcon.asgi.Response, uuid: str
    ) -> None:
        """
        DELETE handler for the /network/connections/uuid/{uuid} endpoint
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

    async def on_get(
        self, _: falcon.asgi.Request, resp: falcon.asgi.Response, id: str
    ) -> None:
        """
        GET handler for the /network/connections/id/{id} endpoint
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

    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response, id: str
    ) -> None:
        """
        PUT handler for the /network/connections/id/{id} endpoint
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

    async def on_patch(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response, id: str
    ) -> None:
        """
        PATCH handler for the /network/connections/id/{id} endpoint
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

    async def on_delete(
        self, _: falcon.asgi.Request, resp: falcon.asgi.Response, id: str
    ) -> None:
        """
        DELETE handler for the /network/connections/id/{id} endpoint
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
