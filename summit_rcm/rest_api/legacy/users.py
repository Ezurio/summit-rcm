#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to handle legacy user management and login requests
"""

import base64
import json
from syslog import syslog
from datetime import datetime
import falcon.asgi
from summit_rcm.settings import ServerConfig, SystemSettingsManage
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.definition import SUMMIT_RCM_ERRORS, USER_PERMISSION_TYPES
from summit_rcm.services.user_service import UserService
from summit_rcm.services.login_service import LoginService, Session

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        DefaultResponseModelLegacy,
        GetUsersResponseModelLegacy,
        InternalServerErrorResponseModel,
        LoginRequestModel,
        LoginResponseModelLegacy,
        NewUserRequestModel,
        UnauthorizedErrorResponseModel,
        UpdateUserRequestModelLegacy,
        UpdateUserResponseModelLegacy,
        UsernameQuery,
    )
    from summit_rcm.rest_api.utils.spectree.tags import login_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    DefaultResponseModelLegacy = None
    GetUsersResponseModelLegacy = None
    InternalServerErrorResponseModel = None
    LoginRequestModel = None
    LoginResponseModelLegacy = None
    NewUserRequestModel = None
    UnauthorizedErrorResponseModel = None
    UpdateUserRequestModelLegacy = None
    UpdateUserResponseModelLegacy = None
    UsernameQuery = None
    login_tag = None


spec = SpectreeService()


class UserManage:
    @spec.validate(
        json=UpdateUserRequestModelLegacy,
        resp=Response(
            HTTP_200=UpdateUserResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[login_tag],
        deprecated=True,
    )
    async def on_put(self, req, resp):
        """
        Update password/permission (legacy)
        """

        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS.get("SDCERR_FAIL"),
            "REDIRECT": 0,
            "InfoMsg": "",
        }

        post_data = await req.get_media()
        username = post_data.get("username", None)
        new_password = post_data.get("new_password", None)

        if not UserService.user_exists(username):
            result["InfoMsg"] = f"user {username} not found"
            resp.media = result
            return

        if new_password:
            current_password = post_data.get("current_password", None)
            if UserService.verify(username, current_password):
                if UserService.update_password(username, new_password):
                    result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
                    # Redirect is required when the default password is updated
                    default_username = (
                        ServerConfig()
                        .get_parser()
                        .get("summit-rcm", "default_username", fallback="root")
                        .strip('"')
                    )
                    default_password = (
                        ServerConfig()
                        .get_parser()
                        .get("summit-rcm", "default_password", fallback="summit")
                        .strip('"')
                    )
                    result["InfoMsg"] = "password changed"
                    if (
                        current_password == default_password
                        and username == default_username
                    ):
                        result["REDIRECT"] = 1
                else:
                    result["InfoMsg"] = "unable to update password"
            else:
                result["InfoMsg"] = "incorrect current password"
        else:
            permission = post_data.get("permission", None)
            if permission:
                if UserService.update_permission(username, permission):
                    result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
                    result["InfoMsg"] = "User logged in"
                else:
                    result["InfoMsg"] = "could not update session"
            else:
                result["InfoMsg"] = "invalid session"
        resp.media = result

    @spec.validate(
        json=NewUserRequestModel,
        resp=Response(
            HTTP_200=DefaultResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[login_tag],
        deprecated=True,
    )
    async def on_post(self, req, resp):
        """Add new user (legacy)"""
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS.get("SDCERR_FAIL"),
            "InfoMsg": "",
        }

        post_data = await req.get_media()
        username = post_data.get("username")
        password = post_data.get("password")
        permission = post_data.get("permission")

        if UserService.user_exists(username):
            result["InfoMsg"] = f"user {username} already exists"
            resp.media = result
            return

        if not username or not password or not permission:
            result["InfoMsg"] = "Missing user name, password, or permission"
            resp.media = result
            return

        if (
            UserService.get_number_of_users()
            < SystemSettingsManage.get_max_web_clients()
        ):
            if UserService.add_user(username, password, permission):
                result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
                result["InfoMsg"] = "User added"
            else:
                result["InfoMsg"] = "failed to add user"
        else:
            result["InfoMsg"] = "Max number of users reached"

        resp.media = result

    @spec.validate(
        query=UsernameQuery,
        resp=Response(
            HTTP_200=DefaultResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[login_tag],
        deprecated=True,
    )
    async def on_delete(self, req, resp):
        """Remove existing user (legacy)"""
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS.get("SDCERR_FAIL"),
            "InfoMsg": "unable to delete user",
        }
        username = req.params.get("username", "")
        default_username = (
            ServerConfig()
            .get_parser()
            .get("summit-rcm", "default_username", fallback="root")
            .strip('"')
        )

        if username == default_username:
            result["InfoMsg"] = f"unable to remove {default_username} user"
        elif not UserService.user_exists(username):
            result["InfoMsg"] = f"user {username} not found"
        elif UserService.delete_user(username):
            result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
            result["InfoMsg"] = "User deleted"

        resp.media = result

    @spec.validate(
        resp=Response(
            HTTP_200=GetUsersResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[login_tag],
        deprecated=True,
    )
    async def on_get(self, _, resp):
        """Retrieve user info (legacy)"""
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS"),
            "InfoMsg": "only non-default users listed under 'Users'",
            "Default_user": ServerConfig()
            .get_parser()
            .get("summit-rcm", "default_username", fallback="root")
            .strip('"'),
        }
        result["Users"] = UserService.get_users_dict()
        result["Count"] = len(result.get("Users"))
        resp.media = result


class LoginManage:
    @spec.validate(
        json=LoginRequestModel,
        resp=Response(
            HTTP_200=LoginResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        tags=[login_tag],
        deprecated=True,
    )
    async def on_post(self, req, resp):
        """Login and retrieve a new session token or refresh an existing one (legacy)"""
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS.get("SDCERR_FAIL", 1),
            "REDIRECT": 0,
            "PERMISSION": "",
            "InfoMsg": "",
        }

        # Check if sessions are enabled
        if not ServerConfig().sessions_enabled:
            result["PERMISSION"] = USER_PERMISSION_TYPES["UserPermissionTypes"]
            result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
            result["InfoMsg"] = "User logged in"
            resp.media = result
            return

        post_data = await req.get_media()
        username = post_data.get("username", "")
        password = post_data.get("password", "")
        syslog(f"Attempt to login user {username}")

        try:
            if (
                hasattr(req.context, "_session")
                and req.context._session
                and req.context.valid_session
                and req.context.session_id
            ):
                # Session cookie exists
                session_id = req.context.session_id
                if not session_id:
                    raise Exception("Malformed cookie")

                if not UserService.verify(username=username, password=password):
                    # Provided username and password are incorrect
                    LoginService().login_failed(username)
                    result["InfoMsg"] = "unable to verify user/password"

                    LoginService().remove_invalid_session(session_id)
                    resp.context.valid_session = False
                    resp.media = result
                    return

                # Provided username and password are correct
                LoginService().login_reset(username)
                result["InfoMsg"] = "User logged in"

                if (
                    username == LoginService().default_username
                    and password == LoginService().default_password
                    and UserService.verify(
                        LoginService().default_username,
                        LoginService().default_password,
                    )
                ):
                    # Password needs changed
                    result["REDIRECT"] = 1
                    result["InfoMsg"] = "Password change required"

                LoginService().keepalive_session(session_id)
                resp.context.valid_session = True
                result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
                syslog(f"User {username} logged in")
                resp.media = result
                return

            # No session cookie present or it's invalid
            if LoginService().is_user_blocked(username):
                resp.context.valid_session = False
                result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_USER_BLOCKED")
                result["InfoMsg"] = "User blocked"
                resp.media = result
                return

            default_login: bool = False
            if (username == LoginService().default_username) and (
                password == LoginService().default_password
            ):
                # Default login
                default_login = True
                if not UserService.get_number_of_users():
                    UserService.add_user(
                        username,
                        password,
                        " ".join(USER_PERMISSION_TYPES["UserPermissionTypes"]),
                    )

            if (
                not LoginService().allow_multiple_user_sessions
                and LoginService().is_user_logged_in(username)
            ):
                result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_USER_LOGGED")
                result["InfoMsg"] = "User already logged in"
                resp.context.valid_session = False
                resp.media = result
                return

            if not (
                default_login
                or UserService.verify(username=username, password=password)
            ):
                # Provided username and password are incorrect
                LoginService().login_failed(username)
                result["InfoMsg"] = "unable to verify user/password"
                resp.context.valid_session = False
                resp.media = result
                return

            # Provided username and password are correct
            LoginService().login_reset(username)
            result["InfoMsg"] = "User logged in"
            resp.context.set_session("USERNAME", username)
            resp.context.set_session("iat", int(round(datetime.utcnow().timestamp())))
            session_base64 = base64.urlsafe_b64encode(
                json.dumps(resp.context._session).encode()
            ).decode()
            LoginService().add_new_valid_session(
                Session(
                    id=session_base64,
                    expiry=int(resp.context._session.get("iat", 0))
                    + (SystemSettingsManage.get_session_timeout() * 60),
                    username=resp.context._session.get("USERNAME", ""),
                )
            )
            resp.context.valid_session = True

            result["PERMISSION"] = UserService.get_permission(username)
            # Don't display "system_user" page for single user mode
            if SystemSettingsManage.get_max_web_clients() == 1 and result["PERMISSION"]:
                result["PERMISSION"] = result["PERMISSION"].replace("system_user", "")

            if (
                username == LoginService().default_username
                and password == LoginService().default_password
                and UserService.verify(
                    LoginService().default_username,
                    LoginService().default_password,
                )
            ):
                # Password needs changed
                result["REDIRECT"] = 1
                result["InfoMsg"] = "Password change required"
            result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
            syslog(f"User {username} logged in")

        except Exception as exception:
            syslog(f"Error while processing login request - {str(exception)}")
            result = {
                "SDCERR": SUMMIT_RCM_ERRORS.get("SDCERR_FAIL", 1),
                "REDIRECT": 0,
                "PERMISSION": "",
                "InfoMsg": "Error while processing login request",
            }
        resp.media = result

    @spec.validate(
        resp=Response(
            HTTP_200=DefaultResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[login_tag],
        deprecated=True,
    )
    async def on_delete(self, req, resp):
        """Log out of an existing session (legacy)"""
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS.get("SDCERR_FAIL", 1),
            "InfoMsg": "",
        }
        username = req.context.get_session("USERNAME")
        if username:
            result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
            result["InfoMsg"] = f"user {username} logged out"
            if not req.context.session_id:
                raise Exception("Malformed cookie")
            LoginService().remove_invalid_session(req.context.session_id)
            syslog(f"logout user {username}")
        else:
            result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_FAIL")
            result["InfoMsg"] = "user not found"
        resp.context.valid_session = False
        resp.media = result
