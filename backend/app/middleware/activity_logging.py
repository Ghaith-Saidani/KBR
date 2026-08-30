from collections.abc import Callable

from fastapi import Request, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.core.database import SessionLocal
from backend.app.services.activity_logger import log_user_activity


class ActivityLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log meaningful HTTP activity performed through the API.

    Logging failures must never break the actual API request.

    The middleware normally creates its own database session.
    Tests can provide a shared session through app.state.
    """

    IGNORED_PATHS = {
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    IGNORED_PREFIXES = (
        "/uploads/",
    )

    SESSION_STATE_KEY = "activity_logging_session"

    def _should_log(
        self,
        path: str,
    ) -> bool:
        """Return whether the request should generate an activity log."""

        if path in self.IGNORED_PATHS:
            return False

        if any(
            path.startswith(prefix)
            for prefix in self.IGNORED_PREFIXES
        ):
            return False

        return True

    def _get_client_ip(
        self,
        request: Request,
    ) -> str | None:
        """Extract the client IP address."""

        if request.client is None:
            return None

        return request.client.host

    def _get_user_id(
        self,
        request: Request,
    ):
        """
        Retrieve the authenticated user ID when available.

        Authentication can expose the authenticated user through
        request.state.user. If it is not available, the activity
        is still logged with user_id=None.
        """

        user = getattr(
            request.state,
            "user",
            None,
        )

        if user is None:
            return None

        return getattr(
            user,
            "id",
            None,
        )

    def _get_database_session(
        self,
        request: Request,
    ) -> tuple[Session, bool]:
        """
        Return the database session used for activity logging.

        Production:
            Create a dedicated SessionLocal session.

        Tests:
            A shared session can be supplied through app.state.

        Returns:
            (session, owns_session)
        """

        shared_session = getattr(
            request.app.state,
            self.SESSION_STATE_KEY,
            None,
        )

        if shared_session is not None:
            return shared_session, False

        return SessionLocal(), True

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """
        Process the request and persist an activity log.
        """

        if not self._should_log(request.url.path):
            return await call_next(request)

        response = None
        exception = None

        try:
            response = await call_next(request)

        except Exception as exc:
            exception = exc
            raise

        finally:
            db = None
            owns_session = False

            try:
                db, owns_session = self._get_database_session(
                    request,
                )

                user_id = self._get_user_id(request)

                status_code = (
                    response.status_code
                    if response is not None
                    else 500
                )

                action = (
                    f"{request.method} "
                    f"{request.url.path}"
                )

                details = f"HTTP {status_code}"

                if exception is not None:
                    details = (
                        "HTTP request failed: "
                        f"{type(exception).__name__}"
                    )

                log_user_activity(
                    db,
                    action=action,
                    user_id=user_id,
                    resource_type="http_request",
                    method=request.method,
                    endpoint=request.url.path,
                    ip_address=self._get_client_ip(
                        request,
                    ),
                    user_agent=request.headers.get(
                        "user-agent",
                    ),
                    details=details,
                    activity_metadata={
                        "status_code": status_code,
                        "query_params": dict(
                            request.query_params,
                        ),
                    },
                )

                db.commit()

            except SQLAlchemyError:
                if db is not None:
                    db.rollback()

            finally:
                if db is not None and owns_session:
                    db.close()

        return response