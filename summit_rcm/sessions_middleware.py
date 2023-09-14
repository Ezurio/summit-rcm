"""
Module for handling 'sessions' as a Falcon middleware
"""

from typing import Any
import base64
import json
import falcon.asgi
from summit_rcm.services.login_service import LoginService


class SessionsMiddleware:
    """
    Middleware to enable sessions
    """

    def __init__(self, session_cookie: str = "session_id") -> None:
        self._session_cookie = session_cookie

    def _load_session_cookie(self, req: falcon.asgi.Request) -> dict:
        try:
            session_cookie = req.get_cookie_values(self._session_cookie)
            if not session_cookie:
                raise Exception("No cookie found")
            return json.loads(
                base64.urlsafe_b64decode(session_cookie[0].encode()).decode()
            )
        except Exception:
            return {}

    async def process_request(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        LoginService().cleanup_expired_sessions()

        req.context.valid_session = False
        session_cookie = req.get_cookie_values(self._session_cookie)
        try:
            if session_cookie:
                LoginService().cleanup_expired_sessions()
                req.context.session_id = session_cookie[0]
                req.context.valid_session = LoginService().session_is_valid(
                    req.context.session_id
                )
        except Exception:
            req.context.valid_session = False
            req.context.session_id = ""

        def get_session(key: str) -> Any:
            if not hasattr(req.context, "_session"):
                req.context._session = self._load_session_cookie(req)
            return req.context._session.get(key, None)

        def set_session(key: str, value: Any) -> None:
            if not hasattr(resp.context, "_session"):
                resp.context._session = self._load_session_cookie(req)
            resp.context._session[key] = value

        def sessions() -> dict:
            if not hasattr(req.context, "_session"):
                req.context._session = self._load_session_cookie(req)
            return req.context._session

        req.context.get_session = get_session
        resp.context.set_session = set_session
        req.context.sessions = sessions

    async def process_request_ws(
        self, req: falcon.asgi.Request, _: falcon.asgi.WebSocket
    ) -> None:
        LoginService().cleanup_expired_sessions()

        req.context.valid_session = False
        session_cookie = req.get_cookie_values(self._session_cookie)
        try:
            if session_cookie:
                LoginService().cleanup_expired_sessions()
                req.context.session_id = session_cookie[0]
                req.context.valid_session = LoginService().session_is_valid(
                    req.context.session_id
                )
        except Exception:
            req.context.valid_session = False
            req.context.session_id = ""

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
        if not (
            req_succeeded
            and hasattr(resp.context, "_session")
            and resp.context._session
            and hasattr(resp.context, "valid_session")
        ):
            resp.context.valid_session = False
            return

        if resp.context.valid_session:
            session_base64 = base64.urlsafe_b64encode(
                json.dumps(resp.context._session).encode()
            ).decode()
            resp.set_cookie(self._session_cookie, session_base64, path="/")
