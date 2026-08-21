from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from backend.app.api.auth import get_current_user
from backend.app.models.user import User, UserRole


def require_roles(
    *allowed_roles: UserRole,
) -> Callable:
    """
    Create a dependency that allows only users
    with one of the specified roles.
    """

    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )

        return current_user

    return role_checker


require_member = require_roles(
    UserRole.MEMBER,
    UserRole.STAFF,
    UserRole.ADMIN,
)

require_staff = require_roles(
    UserRole.STAFF,
    UserRole.ADMIN,
)

require_admin = require_roles(
    UserRole.ADMIN,
)