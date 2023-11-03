"""Module to handle user management"""

from syslog import LOG_ERR, syslog
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.services.user_service import UserService

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        BadRequestErrorResponseModel,
        ConflictErrorResponseModel,
        ForbiddenErrorResponseModel,
        InternalServerErrorResponseModel,
        NewUserRequestModel,
        NotFoundErrorResponseModel,
        UnauthorizedErrorResponseModel,
        UpdateUserRequestModel,
        UserResponseModel,
        UsersResponseModel,
    )
    from summit_rcm.rest_api.utils.spectree.tags import login_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    BadRequestErrorResponseModel = None
    ConflictErrorResponseModel = None
    ForbiddenErrorResponseModel = None
    InternalServerErrorResponseModel = None
    NewUserRequestModel = None
    NotFoundErrorResponseModel = None
    UnauthorizedErrorResponseModel = None
    UpdateUserRequestModel = None
    UserResponseModel = None
    UsersResponseModel = None
    login_tag = None


spec = SpectreeService()


class UsersResource:
    """Resource to handle queries and requests for user management"""

    @spec.validate(
        resp=Response(
            HTTP_200=UsersResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[login_tag],
    )
    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        Retrieve a list of the current users
        """
        try:
            users = []
            for username, permissions in UserService.get_users_dict().items():
                users.append({"username": username, "permissions": permissions})
            resp.media = users
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to retrieve users information: {str(exception)}")
            resp.status = falcon.HTTP_500

    @spec.validate(
        json=NewUserRequestModel,
        resp=Response(
            HTTP_201=UserResponseModel,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_409=ConflictErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[login_tag],
    )
    async def on_post(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        Add a new user
        """
        try:
            post_data = await req.get_media()
            username = post_data.get("username")
            password = post_data.get("password")
            permissions = post_data.get("permissions")

            if (
                not username or not password or not permissions
            ) or UserService.user_exists(username):
                resp.status = falcon.HTTP_400
                return

            if UserService.max_users_reached():
                # Max number of allowed users reached, so return a 409 (Conflict) status code
                resp.status = falcon.HTTP_409
                return

            if not UserService.add_user(username, password, permissions):
                resp.status = falcon.HTTP_500
                return

            resp.media = {
                "username": username,
                "permissions": UserService.get_permission(username),
            }
            resp.status = falcon.HTTP_201
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to add new user: {str(exception)}")
            resp.status = falcon.HTTP_500


class UserResource:
    """Resource to handle queries and requests for a specific user"""

    @spec.validate(
        resp=Response(
            HTTP_200=UserResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[login_tag],
    )
    async def on_get(
        self, _: falcon.asgi.Request, resp: falcon.asgi.Response, username: str
    ) -> None:
        """
        Retrieve details about a specified user
        """
        try:
            if not UserService.user_exists(username):
                resp.status = falcon.HTTP_404
                return

            resp.media = {
                "username": username,
                "permissions": UserService.get_permission(username),
            }
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to retrieve user information: {str(exception)}")
            resp.status = falcon.HTTP_500

    @spec.validate(
        json=UpdateUserRequestModel,
        resp=Response(
            HTTP_200=UserResponseModel,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_403=ForbiddenErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[login_tag],
    )
    async def on_patch(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response, username: str
    ) -> None:
        """
        Update the configuration of a specified user
        """
        try:
            put_data = await req.get_media()
            new_password = put_data.get("newPassword")
            current_password = put_data.get("currentPassword")
            permissions = put_data.get("permissions")

            if (
                not current_password
                or not username
                or (not new_password and not permissions)
            ):
                resp.status = falcon.HTTP_400
                return

            if not UserService.user_exists(username):
                resp.status = falcon.HTTP_404
                return

            if new_password:
                if not UserService.verify(username, current_password):
                    resp.status = falcon.HTTP_403
                    return

                if not UserService.update_password(username, new_password):
                    resp.status = falcon.HTTP_500
                    return

            if permissions and not UserService.update_permission(username, permissions):
                resp.status = falcon.HTTP_500
                return

            resp.media = {
                "username": username,
                "permissions": UserService.get_permission(username),
            }
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to update user: {str(exception)}")
            resp.status = falcon.HTTP_500

    @spec.validate(
        resp=Response(
            HTTP_200=None,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[login_tag],
    )
    async def on_delete(
        self, _: falcon.asgi.Request, resp: falcon.asgi.Response, username: str
    ) -> None:
        """
        Remove a specified user
        """
        try:
            if not UserService.user_exists(username):
                resp.status = falcon.HTTP_404
                return

            if not UserService.delete_user(username):
                resp.status = falcon.HTTP_500
                return

            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to delete user: {str(exception)}")
            resp.status = falcon.HTTP_500
