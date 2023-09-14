"""Module to handle login session management"""

import base64
import json
from syslog import LOG_ERR, syslog
from datetime import datetime
import falcon.asgi
from summit_rcm.definition import USER_PERMISSION_TYPES
from summit_rcm.services.login_service import LoginService, MAX_SESSION_AGE_S, Session
from summit_rcm.services.user_service import UserService


class LoginResource:
    """Resource to handle queries and requests for login session management"""

    async def on_post(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        POST handler for the /login endpoint
        """
        try:
            if not LoginService().sessions_enabled:
                # If sessions aren't enabled, then the login request is "successful"
                resp.status = falcon.HTTP_200
                return

            post_data = await req.get_media()
            username = post_data.get("username", "")
            password = post_data.get("password", "")

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
                    LoginService().remove_invalid_session(session_id)
                    resp.context.valid_session = False
                    resp.status = falcon.HTTP_403
                    return

                # Provided username and password are correct
                LoginService().login_reset(username)
                LoginService().keepalive_session(session_id)
                resp.context.valid_session = True
                syslog(f"User {username} logged in")
                resp.status = falcon.HTTP_200
                return

            # No session cookie present or it's invalid
            if LoginService().is_user_blocked(username):
                resp.context.valid_session = False
                resp.status = falcon.HTTP_403
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
                resp.context.valid_session = False
                resp.status = falcon.HTTP_403
                return

            if not (
                default_login
                or UserService.verify(username=username, password=password)
            ):
                # Provided username and password are incorrect
                LoginService().login_failed(username)
                resp.context.valid_session = False
                resp.status = falcon.HTTP_403
                return

            # Provided username and password are correct
            LoginService().login_reset(username)
            resp.context.set_session("USERNAME", username)
            resp.context.set_session("iat", int(round(datetime.utcnow().timestamp())))
            session_base64 = base64.urlsafe_b64encode(
                json.dumps(resp.context._session).encode()
            ).decode()
            LoginService().add_new_valid_session(
                Session(
                    id=session_base64,
                    expiry=int(resp.context._session.get("iat", 0)) + MAX_SESSION_AGE_S,
                    username=resp.context._session.get("USERNAME", ""),
                )
            )
            resp.context.valid_session = True
            resp.status = falcon.HTTP_200
            syslog(f"User {username} logged in")
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to login: {str(exception)}")
            resp.status = falcon.HTTP_500

    async def on_delete(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        DELETE handler for the /login endpoint
        """
        try:
            username = req.context.get_session("USERNAME")
            if not username:
                resp.status = falcon.HTTP_400
                return

            if not req.context.session_id:
                raise Exception("Malformed cookie")

            LoginService().remove_invalid_session(req.context.session_id)
            resp.status = falcon.HTTP_200
            syslog(f"logout user {username}")
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to logout: {str(exception)}")
            resp.status = falcon.HTTP_500
