"""
Module to handle session login management
"""

from datetime import datetime
from threading import Lock
from typing import List
from summit_rcm.settings import (
    ServerConfig,
    SystemSettingsManage,
)
from summit_rcm.utils import Singleton

MAX_SESSION_AGE_S = 60 * 10
"""
Maximum session age in seconds (10 minutes)
"""


class Session:
    """Data class to hold info about a session"""

    id: str
    expiry: int
    username: str

    def __init__(self, id: str, expiry: int, username: str) -> None:
        self.id = id
        self.expiry = expiry
        self.username = username


class LoginService(metaclass=Singleton):
    """Service to handle session login management"""

    _lock = Lock()
    # Record logins with wrong credentials to protect against tamper
    _failed_logins = {}
    _valid_sessions: list[Session] = []

    def __init__(self) -> None:
        # self._sessions_enabled = (
        #     ServerConfig()
        #     .get_parser()
        #     .getboolean("/", "tools.sessions.on", fallback=True)
        # )
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

    # @property
    # def sessions_enabled(self) -> bool:
    #     """Whether or not sessions are enabled"""
    #     return self._sessions_enabled

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

    @property
    def valid_sessions(self) -> List[Session]:
        """List of valid sessions"""
        return self._valid_sessions

    def is_user_blocked(self, username: str) -> bool:
        """Retrieve whether or not the user with the specified username is blocked"""

        user = {}
        with self._lock:
            now = datetime.now()
            user = self._failed_logins.get(username)
            # Block username for 'login_block_timeout' seconds if failed consecutively for
            # 'login_retry_times' times
            if (
                user
                and len(user["time"]) >= SystemSettingsManage.get_login_retry_times()
            ):
                dt = abs((now - user["time"][-1]).total_seconds())
                if dt < SystemSettingsManage.get_tamper_protection_timeout():
                    return True
                self._failed_logins.pop(username, None)
        return False

    def login_failed(self, username: str):
        """Handle the event when a login attempt failed"""

        with self._lock:
            now = datetime.now()
            user = self._failed_logins.get(username, {})
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
            self._failed_logins[username] = user

    def login_reset(self, username: str):
        """Handle the event when a user's login session is reset"""

        with self._lock:
            self._failed_logins.pop(username, None)

    def is_user_logged_in(self, username: str) -> bool:
        """Retrieve whether or not the user with the specified username is currently logged in"""

        for session in self.valid_sessions:
            if session.username == username:
                return True
        return False

    def add_new_valid_session(self, new_session: Session):
        """Add a new valid session to the list"""
        self._valid_sessions.append(new_session)

    def remove_invalid_session(self, invalid_session_id: int) -> None:
        """Remove an invalid session from the list"""
        self._valid_sessions[:] = [
            x for x in self._valid_sessions if x.id != invalid_session_id
        ]

    def cleanup_expired_sessions(self) -> None:
        """
        Clean up and remove any expired sessions. If multiple sessions per user is not enabled, also
        log out the corresponding user.
        """
        now = int(round(datetime.utcnow().timestamp()))
        self._valid_sessions[:] = [x for x in self._valid_sessions if now < x.expiry]

    def keepalive_session(self, session_id: str) -> None:
        """Update the expiry for the session with the given ID"""
        now = int(round(datetime.utcnow().timestamp()))
        for session in self._valid_sessions:
            if session.id == session_id:
                session.expiry = now + MAX_SESSION_AGE_S
                return

    def session_is_valid(self, session_id: str) -> bool:
        """
        Determine whether or not the session with the given ID is valid.
        """
        now = int(round(datetime.utcnow().timestamp()))
        for session in self.valid_sessions:
            if session_id == session.id and now < session.expiry:
                # Target session is not expired
                return True

        return False
