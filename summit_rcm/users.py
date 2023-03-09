import secrets
import falcon
import uuid
import hashlib
from threading import Lock
from datetime import datetime
from .definition import SUMMIT_RCM_ERRORS, USER_PERMISSION_TYPES
from .settings import ServerConfig, SummitRCMConfigManage, SystemSettingsManage
from syslog import syslog


class UserManageHelper(object):
    @classmethod
    def verify(cls, username, password):
        key = SummitRCMConfigManage.get_key_from_section(username, "salt")
        if not key:
            return False

        attempt = hashlib.sha256(key.encode() + password.encode()).hexdigest()
        return attempt == SummitRCMConfigManage.get_key_from_section(
            username, "password", None
        )

    @classmethod
    def user_exists(cls, username):
        return SummitRCMConfigManage.verify_section(username)

    @classmethod
    def delUser(cls, username):
        if SummitRCMConfigManage.remove_section(username):
            return SummitRCMConfigManage.save()
        return False

    @classmethod
    def addUser(cls, username, password, permission=None):
        if SummitRCMConfigManage.add_section(username):
            salt = uuid.uuid4().hex
            SummitRCMConfigManage.update_key_from_section(username, "salt", salt)
            SummitRCMConfigManage.update_key_from_section(
                username,
                "password",
                hashlib.sha256(salt.encode() + password.encode()).hexdigest(),
            )
            if permission:
                SummitRCMConfigManage.update_key_from_section(
                    username, "permission", permission
                )
            return SummitRCMConfigManage.save()
        return False

    @classmethod
    def updatePassword(cls, username, password):
        if SummitRCMConfigManage.get_key_from_section(username, "salt", None):
            salt = uuid.uuid4().hex
            SummitRCMConfigManage.update_key_from_section(username, "salt", salt)
            SummitRCMConfigManage.update_key_from_section(
                username,
                "password",
                hashlib.sha256(salt.encode() + password.encode()).hexdigest(),
            )
            return SummitRCMConfigManage.save()
        return False

    @classmethod
    def getPermission(cls, username):
        return SummitRCMConfigManage.get_key_from_section(username, "permission", None)

    @classmethod
    def updatePermission(cls, username, permission):
        if permission and SummitRCMConfigManage.get_key_from_section(
            username, "permission", None
        ):
            return SummitRCMConfigManage.update_key_from_section(
                username, "permission", permission
            )
        return False

    @classmethod
    def getNumberOfUsers(cls):
        """All users including root"""
        return SummitRCMConfigManage.get_section_size_by_key("password")

    @classmethod
    def getUserList(cls):
        userlist = SummitRCMConfigManage.get_sections_and_key("permission")
        if userlist:
            # Default user shouldn't be listed as its permission can't be updated by Summit RCM
            default_username = (
                ServerConfig()
                .get_parser()
                .get("summit-rcm", "default_username", fallback="root")
                .strip('"')
            )
            userlist.pop(default_username, None)
        return userlist


class UserManage:
    async def on_put(self, req, resp):
        """
        Update password/permission
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

        if not UserManageHelper.user_exists(username):
            result["InfoMsg"] = f"user {username} not found"
            resp.media = result
            return

        if new_password:
            current_password = post_data.get("current_password", None)
            if UserManageHelper.verify(username, current_password):
                if UserManageHelper.updatePassword(username, new_password):
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
                if UserManageHelper.updatePermission(username, permission):
                    result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
                    result["InfoMsg"] = "User logged in"
                else:
                    result["InfoMsg"] = "could not update session"
            else:
                result["InfoMsg"] = "invalid session"
        resp.media = result

    async def on_post(self, req, resp):
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

        if UserManageHelper.user_exists(username):
            result["InfoMsg"] = f"user {username} already exists"
            resp.media = result
            return

        if not username or not password or not permission:
            result["InfoMsg"] = "Missing user name, password, or permission"
            resp.media = result
            return

        if (
            UserManageHelper.getNumberOfUsers()
            < SystemSettingsManage.get_max_web_clients()
        ):
            if UserManageHelper.addUser(username, password, permission):
                result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
                result["InfoMsg"] = "User added"
            else:
                result["InfoMsg"] = "failed to add user"
        else:
            result["InfoMsg"] = "Max number of users reached"

        resp.media = result

    async def on_delete(self, req, resp):
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
        elif not UserManageHelper.user_exists(username):
            result["InfoMsg"] = f"user {username} not found"
        elif UserManageHelper.delUser(username):
            result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
            result["InfoMsg"] = "User deleted"

        resp.media = result

    async def on_get(self, req, resp):
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
        result["Users"] = UserManageHelper.getUserList()
        result["Count"] = len(result.get("Users"))
        resp.media = result


class LoginManageHelper(object):

    _lock = Lock()
    # Record logins with wrong credentials to protect against tamper
    _failed_logins = {}
    # Record successful logins and delete inactive sessions
    _sessions = {}

    @classmethod
    def is_user_blocked(cls, username):
        user = {}
        with cls._lock:
            now = datetime.now()
            user = cls._failed_logins.get(username)
            # Block username for 'login_block_timeout' seconds if failed consecutively for 'login_retry_times' times
            if (
                user
                and len(user["time"]) >= SystemSettingsManage.get_login_retry_times()
            ):
                dt = abs((now - user["time"][-1]).total_seconds())
                if dt < SystemSettingsManage.get_tamper_protection_timeout():
                    return True
                cls._failed_logins.pop(username, None)
        return False

    @classmethod
    def login_failed(cls, username):
        with cls._lock:
            now = datetime.now()
            user = cls._failed_logins.get(username, {})
            if user:
                user["time"] = [
                    dt
                    for dt in user["time"]
                    if abs((now - dt).total_seconds())
                    < SystemSettingsManage.get_login_retry_window()
                ]
                if len(user["time"]) >= SystemSettingsManage.get_login_retry_times():
                    user["time"].pop(0, None)
            else:
                user["time"] = []

            user["time"].append(now)
            cls._failed_logins[username] = user

    @classmethod
    def login_reset(cls, username):
        with cls._lock:
            cls._failed_logins.pop(username, None)

    @classmethod
    def is_user_logged_in(cls, username):

        with cls._lock:

            # temp_id = cherrypy.session.id
            # for user, sid in cls._sessions.copy().items():
            #     cherrypy.session.id = sid
            #     if not cherrypy.session._exists():
            #         cls._sessions.pop(user, None)
            # cherrypy.session.id = temp_id

            if cls._sessions.get(username, None):
                return True

            cls._sessions[username] = secrets.token_bytes(10)
        return False

    @classmethod
    def delete(cls, username):
        cls._sessions.pop(username, None)


class LoginManage:
    def __init__(self) -> None:
        self._sessions_enabled = (
            ServerConfig()
            .get_parser()
            .getboolean("/", "tools.sessions.on", fallback=True)
        )
        self._default_username = (
            ServerConfig()
            .get_parser()
            .get("summit-rcm", "default_username", fallback="root")
            .strip('"')
        )
        self._default_password = (
            ServerConfig()
            .get_parser()
            .get("summit-rcm", "default_password", fallback="summit")
            .strip('"')
        )
        self._allow_multiple_user_sessions = (
            ServerConfig()
            .get_parser()
            .getboolean("summit-rcm", "allow_multiple_user_sessions", fallback=False)
        )

    async def on_post(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS.get("SDCERR_FAIL", 1),
            "REDIRECT": 0,
            "PERMISSION": "",
            "InfoMsg": "",
        }

        # Check if sessions are enabled
        if not self._sessions_enabled:
            result["PERMISSION"] = USER_PERMISSION_TYPES["UserPermissionTypes"]
            result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
            result["InfoMsg"] = "User logged in"
            resp.media = result
            return

        post_data = await req.get_media()
        username = post_data.get("username", "")
        password = post_data.get("password", "")
        syslog(f"Attempt to login user {username}")

        # Return if username is blocked
        username_from_cookie = req.get_cookie_values("USERNAME")
        if not username_from_cookie:
            if LoginManageHelper.is_user_blocked(username):
                result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_USER_BLOCKED")
                result["InfoMsg"] = "User blocked"
                resp.media = result
                return

        # If default password is not changed, redirect to passwd update page.
        if (username == self._default_username) and (
            password == self._default_password
        ):

            cnt = UserManageHelper.getNumberOfUsers()
            if not cnt:
                UserManageHelper.addUser(
                    username,
                    password,
                    " ".join(USER_PERMISSION_TYPES["UserPermissionTypes"]),
                )

            if not cnt or UserManageHelper.verify(
                self._default_username, self._default_password
            ):

                LoginManageHelper.login_reset(username)
                if (
                    LoginManageHelper.is_user_logged_in(username)
                    and not self._allow_multiple_user_sessions
                ):
                    result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_USER_LOGGED")
                    result["InfoMsg"] = "User already logged in"
                    resp.media = result
                    return

                req.set_cookie("USERNAME", username)
                result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
                result["REDIRECT"] = 1
                result["InfoMsg"] = "Password change required"
                syslog(f"User {username} logged in")
                resp.media = result
                return

        # Session is created, but default password was not changed.
        if username == self._default_username:
            if UserManageHelper.verify(self._default_username, self._default_password):
                result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
                result["REDIRECT"] = 1
                result["InfoMsg"] = "Password change required"
                syslog(f"User {username} logged in")
                resp.media = result
                return

        # If session already exists, return success (if multiple user sessions not allowed);
        # otherwise verify login username and password.
        if not cherrypy.session.get("USERNAME", None) or cherrypy.request.app.config[
            "summit-rcm"
        ].get("allow_multiple_user_sessions", False):
            if not UserManageHelper.verify(username, password):
                LoginManageHelper.login_failed(username)
                result["InfoMsg"] = "unable to verify user/password"

                # Expire the current session if user has already logged in
                # if cherrypy.session.get("USERNAME", None):
                #     cherrypy.lib.sessions.expire()
                # return result
                resp.media = result
                return

            LoginManageHelper.login_reset(username)

        if (
            LoginManageHelper.is_user_logged_in(username)
            and not self._allow_multiple_user_sessions
        ):
            result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_USER_LOGGED")
            result["InfoMsg"] = "User already logged in"
            resp.media = result
            return

        resp.set_cookie("USERNAME", username)

        result["PERMISSION"] = UserManageHelper.getPermission(username)
        # Don't display "system_user" page for single user mode
        if SystemSettingsManage.get_max_web_clients() == 1 and result["PERMISSION"]:
            result["PERMISSION"] = result["PERMISSION"].replace("system_user", "")

        result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
        result["InfoMsg"] = "User logged in"
        syslog(f"user {username} logged in")
        resp.media = result
        return

    async def DELETE(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS.get("SDCERR_FAIL", 1),
            "InfoMsg": "",
        }
        # username = cherrypy.session.pop("USERNAME", None)
        username = req.get_cookie_values("USERNAME")
        if username:
            LoginManageHelper.delete(username)
            result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
            result["InfoMsg"] = f"user {username} logged out"
            syslog(f"logout user {username}")
        else:
            result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_FAIL")
            result["InfoMsg"] = "user not found"
        resp.media = result
        return
