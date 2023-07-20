from datetime import datetime
from typing import Any
import falcon.asgi
import base64
import json
import asyncio


EXPIRED_SESSION_CLEANUP_INTERNVAL_S = 60 * 5
"""
Interval (in seconds) between calls to clean up expired sessions
"""

MAX_SESSION_AGE_S = 60 * 10
"""
Maximum session age in seconds (10 minutes)
"""


class Session:
    id: str
    expiry: int

    def __init__(self, id: str, expiry: int) -> None:
        self.id = id
        self.expiry = expiry


class SessionsMiddleware:
    """
    Middleware to enable sessions
    """

    def __init__(self, session_cookie: str = "session_id") -> None:
        self._session_cookie = session_cookie
        self._valid_sessions: list[Session] = []

        asyncio.get_event_loop().call_later(
            EXPIRED_SESSION_CLEANUP_INTERNVAL_S, self._cleanup_expired_sessions
        )

    def _cleanup_expired_sessions(self) -> None:
        now = int(round(datetime.utcnow().timestamp()))
        self._valid_sessions[:] = [x for x in self._valid_sessions if now < x.expiry]

        asyncio.get_event_loop().call_later(
            EXPIRED_SESSION_CLEANUP_INTERNVAL_S, self._cleanup_expired_sessions
        )

    def _load_session_cookie(self, req: falcon.asgi.Request) -> dict:
        session_cookie = req.get_cookie_values(self._session_cookie)
        if session_cookie:
            try:
                payload = json.loads(
                    base64.urlsafe_b64decode(session_cookie[0].encode()).decode()
                )
            except Exception:
                payload = {}
        else:
            payload = {}

        return payload

    async def process_request(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        req.context.valid_session = False
        session_cookie = req.get_cookie_values(self._session_cookie)
        if session_cookie:
            try:
                session_id_base64 = session_cookie[0]
                now = int(round(datetime.utcnow().timestamp()))
                for session in self._valid_sessions:
                    if session_id_base64 == session.id and now < session.expiry:
                        req.context.valid_session = True
                        break
            except Exception:
                req.context.valid_session = False

        def get_session(key: str) -> Any:
            if not hasattr(resp.context, "_session"):
                resp.context._session = self._load_session_cookie(req)
            return resp.context._session.get(key, None)

        def set_session(key: str, value: Any) -> None:
            if not hasattr(resp.context, "_session"):
                resp.context._session = self._load_session_cookie(req)
            resp.context._session[key] = value

        def sessions() -> dict:
            if not hasattr(resp.context, "_session"):
                resp.context._session = self._load_session_cookie(req)
            return resp.context._session

        req.context.get_session = get_session
        resp.context.set_session = set_session
        req.context.sessions = sessions

    async def process_request_ws(
        self, req: falcon.asgi.Request, _: falcon.asgi.WebSocket
    ) -> None:
        req.context.valid_session = False
        session_cookie = req.get_cookie_values(self._session_cookie)
        if session_cookie:
            try:
                session_id_base64 = session_cookie[0]
                now = int(round(datetime.utcnow().timestamp()))
                for session in self._valid_sessions:
                    if session_id_base64 == session.id and now < session.expiry:
                        req.context.valid_session = True
                        break
            except Exception:
                req.context.valid_session = False

        def get_session(key: str) -> Any:
            if not hasattr(req.context, "_session"):
                req.context._session = self._load_session_cookie(req)
            return req.context._session.get(key, None)

        req.context.get_session = get_session

    async def process_response(
        self,
        req: falcon.asgi.Request,
        resp: falcon.asgi.Response,
        resource,
        req_succeeded: bool,
    ) -> None:
        if (
            req_succeeded
            and hasattr(resp.context, "_session")
            and resp.context._session
        ):
            session_base64 = base64.urlsafe_b64encode(
                json.dumps(resp.context._session).encode()
            ).decode()
            resp.set_cookie(self._session_cookie, session_base64, path="/")
            if hasattr(resp.context, "valid_session"):
                if resp.context.valid_session:
                    session_found = False
                    for session in self._valid_sessions:
                        if session.id == session_base64:
                            session_found = True
                            break
                    if not session_found:
                        self._valid_sessions.append(
                            Session(
                                id=session_base64,
                                expiry=int(resp.context._session.get("iat", 0))
                                + MAX_SESSION_AGE_S,
                            )
                        )
                else:
                    self._valid_sessions[:] = [
                        x for x in self._valid_sessions if x.id != session_base64
                    ]
            else:
                resp.context.valid_session = False
        else:
            resp.context.valid_session = False
