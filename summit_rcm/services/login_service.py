"""
Module to handle session login management
"""

from datetime import datetime
import secrets
from threading import Lock
from summit_rcm.settings import (
    ServerConfig,
    SystemSettingsManage,
)
from summit_rcm.utils import Singleton


class LoginService(metaclass=Singleton):
    """Service to handle session login management"""

    _lock = Lock()
    # Record logins with wrong credentials to protect against tamper
    _failed_logins = {}
    # Record successful logins and delete inactive sessions
    _sessions = {}

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

    @property
    def sessions_enabled(self) -> bool:
        """Whether or not sessions are enabled"""
        return self._sessions_enabled

    @property
    def default_username(self) -> str:
        """Default username"""
        return self._default_username

    @property
    def default_password(self) -> str:
        """Default password"""
        return self._default_password

    @property
    def allow_multiple_user_sessions(self) -> bool:
        """Whether or not multiple sessions per user are enabled"""
        return self._allow_multiple_user_sessions

    @classmethod
    def is_user_blocked(cls, username: str) -> bool:
        """Retrieve whether or not the user with the specified username is blocked"""

        user = {}
        with cls._lock:
            now = datetime.now()
            user = cls._failed_logins.get(username)
            # Block username for 'login_block_timeout' seconds if failed consecutively for
            # 'login_retry_times' times
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
    def login_failed(cls, username: str):
        """Handle the event when a login attempt failed"""

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
    def login_reset(cls, username: str):
        """Handle the event when a user's login session is reset"""

        with cls._lock:
            cls._failed_logins.pop(username, None)

    @classmethod
    def is_user_logged_in(cls, username: str) -> bool:
        """Retrieve whether or not the user with the specified username is currently logged in"""

        with cls._lock:
            if cls._sessions.get(username, None):
                return True

            cls._sessions[username] = secrets.token_bytes(10)
        return False

    @classmethod
    def delete(cls, username):
        """Remove the active session for the user with the specified username"""

        cls._sessions.pop(username, None)
