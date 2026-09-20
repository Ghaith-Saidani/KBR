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
        "/auth/me",
        "/notifications/unread-count",
        "/admin/activity-logs",
    }

    IGNORED_PREFIXES = (
        "/uploads/",
    )

    SESSION_STATE_KEY = "activity_logging_session"

    ACTION_MAP = {
        ("POST", "/auth/login"): (
            "LOGIN",
            "authentication",
        ),
        ("POST", "/auth/register"): (
            "REGISTER",
            "authentication",
        ),
        ("POST", "/auth/dev/activate"): (
            "USER_ACTIVATED",
            "authentication",
        ),
    }

    def _should_log(
        self,
        request: Request,
    ) -> bool:
        """Return whether the request should generate an activity log."""

        path = request.url.path

        # OPTIONS requests are browser/CORS infrastructure traffic.
        if request.method.upper() == "OPTIONS":
            return False

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

    def _get_resource_type(
        self,
        path: str,
    ) -> str:
        """
        Derive a basic resource type from the request path.

        Infrastructure endpoints such as health checks are classified
        as generic HTTP requests.

        Examples:
            /health             -> http_request
            /health/db         -> http_request
            /admin/members     -> members
            /events            -> events
            /news/123          -> news
            /admin/events/123  -> events
        """

        infrastructure_paths = {
            "/health",
            "/health/db",
        }

        if path in infrastructure_paths:
            return "http_request"

        parts = [
            part
            for part in path.strip("/").split("/")
            if part
        ]

        if not parts:
            return "http_request"

        # Remove administrative/API grouping prefixes.
        while parts and parts[0] in {
            "admin",
            "api",
        }:
            parts.pop(0)

        if not parts:
            return "http_request"

        resource = parts[0]

        return resource.replace(
            "-",
            "_",
        )

    def _get_action(
        self,
        method: str,
        path: str,
    ) -> tuple[str, str]:
        """
        Determine a meaningful activity action and resource type.
        """

        normalized_method = method.upper()

        # Dynamic development activation route:
        # /auth/dev/activate/{user_id}
        if (
            normalized_method == "POST"
            and path.startswith("/auth/dev/activate/")
        ):
            return (
                "USER_ACTIVATED",
                "authentication",
            )

        # Exact action mappings for important authentication events.
        mapped_action = self.ACTION_MAP.get(
            (
                normalized_method,
                path,
            )
        )

        if mapped_action is not None:
            return mapped_action

        resource_type = self._get_resource_type(
            path,
        )

        # Keep the original HTTP action format for generic requests.
        # This preserves compatibility with the existing audit-log
        # contract while explicit business actions use semantic names.
        return (
            f"{normalized_method} {path}",
            resource_type,
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
            return (
                shared_session,
                False,
            )

        return (
            SessionLocal(),
            True,
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """
        Process the request and persist an activity log.
        """

        if not self._should_log(request):
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
                db, owns_session = (
                    self._get_database_session(
                        request,
                    )
                )

                user_id = self._get_user_id(
                    request,
                )

                status_code = (
                    response.status_code
                    if response is not None
                    else 500
                )

                action, resource_type = (
                    self._get_action(
                        request.method,
                        request.url.path,
                    )
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
                    resource_type=resource_type,
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