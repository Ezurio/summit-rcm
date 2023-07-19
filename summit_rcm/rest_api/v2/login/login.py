"""Module to handle login session management"""

from syslog import LOG_ERR, syslog
from datetime import datetime
import falcon.asgi
from summit_rcm.definition import USER_PERMISSION_TYPES
from summit_rcm.services.login_service import LoginService
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

            # Return if username is blocked
            username_from_cookie = req.context.get_session("USERNAME")
            if not username_from_cookie and LoginService().is_user_blocked(username):
                resp.status = falcon.HTTP_403
                return

            # If default password is not changed, redirect to password update page.
            if (username == LoginService().default_username) and (
                password == LoginService().default_password
            ):
                count = UserService.get_number_of_users()
                if not count:
                    UserService.add_user(
                        username,
                        password,
                        " ".join(USER_PERMISSION_TYPES["UserPermissionTypes"]),
                    )

                if not count or UserService.verify(
                    LoginService().default_username, LoginService().default_password
                ):
                    LoginService().login_reset(username)
                    if (
                        LoginService().is_user_logged_in(username)
                        and not LoginService().allow_multiple_user_sessions
                    ):
                        # User already logged in
                        resp.status = falcon.HTTP_200
                        return

                    resp.context.set_session("USERNAME", username)
                    resp.context.set_session(
                        "iat", int(round(datetime.utcnow().timestamp()))
                    )
                    resp.context.valid_session = True
                    syslog(f"User {username} logged in")
                    resp.status = falcon.HTTP_200
                    return

            # Session is created, but default password was not changed.
            if username == LoginService().default_username:
                if UserService.verify(
                    LoginService().default_username, LoginService().default_password
                ):
                    syslog(f"User {username} logged in")
                    resp.status = falcon.HTTP_200
                    return

            # If session already exists, return success (if multiple user sessions not allowed);
            # otherwise verify login username and password.
            if (
                not req.context.get_session("USERNAME")
                or LoginService().allow_multiple_user_sessions
            ):
                if not UserService.verify(username, password):
                    LoginService().login_failed(username)
                    # Expire the current session if user has already logged in
                    resp.context.valid_session = False
                    resp.status = falcon.HTTP_403
                    return

                LoginService().login_reset(username)

            if (
                LoginService().is_user_logged_in(username)
                and not LoginService().allow_multiple_user_sessions
            ):
                # User already logged in
                resp.status = falcon.HTTP_400
                return

            resp.context.set_session("USERNAME", username)
            resp.context.set_session("iat", int(round(datetime.utcnow().timestamp())))
            resp.context.valid_session = True
            resp.status = falcon.HTTP_200
            syslog(f"user {username} logged in")
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

            LoginService().delete(username)
            resp.context.valid_session = False
            resp.status = falcon.HTTP_200
            syslog(f"logout user {username}")
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to logout: {str(exception)}")
            resp.status = falcon.HTTP_500
