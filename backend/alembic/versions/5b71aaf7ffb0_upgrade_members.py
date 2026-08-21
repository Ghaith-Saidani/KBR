"""upgrade members

Revision ID: 5b71aaf7ffb0
Revises: d17b867dde9e
Create Date: 2026-08-21 13:57:57.358084

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5b71aaf7ffb0"
down_revision: Union[str, Sequence[str], None] = "d17b867dde9e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade the members table."""

    # Add the new columns as nullable first so existing
    # member records can be populated safely.
    op.add_column(
        "members",
        sa.Column(
            "slug",
            sa.String(length=180),
            nullable=True,
        ),
    )

    op.add_column(
        "members",
        sa.Column(
            "position",
            sa.String(length=150),
            nullable=True,
        ),
    )

    # Create the PostgreSQL enum type before using it.
    member_status = sa.Enum(
        "ACTIVE",
        "INACTIVE",
        "ARCHIVED",
        name="member_status",
    )

    member_status.create(
        op.get_bind(),
        checkfirst=True,
    )

    op.add_column(
        "members",
        sa.Column(
            "status",
            member_status,
            nullable=True,
        ),
    )

    # Populate slugs for existing members.
    #
    # The first pass creates a normalized slug from the
    # existing first/last name.
    op.execute(
        """
        UPDATE members
        SET slug = lower(
            regexp_replace(
                trim(
                    regexp_replace(
                        first_name || '-' || last_name,
                        '[^a-zA-Z0-9]+',
                        '-',
                        'g'
                    )
                ),
                '^-+|-+$',
                '',
                'g'
            )
        )
        WHERE slug IS NULL
        """
    )

    # Handle empty/null results.
    op.execute(
        """
        UPDATE members
        SET slug = 'member-' || substr(id::text, 1, 8)
        WHERE slug IS NULL OR slug = ''
        """
    )

    # Resolve duplicate slugs deterministically.
    op.execute(
        """
        WITH duplicates AS (
            SELECT
                id,
                slug,
                ROW_NUMBER() OVER (
                    PARTITION BY slug
                    ORDER BY created_at, id
                ) AS row_number
            FROM members
        )
        UPDATE members AS m
        SET slug =
            CASE
                WHEN d.row_number = 1
                    THEN d.slug
                ELSE d.slug || '-' || d.row_number::text
            END
        FROM duplicates AS d
        WHERE m.id = d.id
          AND d.row_number > 1
        """
    )

    # Existing members become active by default.
    op.execute(
        """
        UPDATE members
        SET status = 'ACTIVE'
        WHERE status IS NULL
        """
    )

    # Now enforce the model constraints.
    op.alter_column(
        "members",
        "slug",
        nullable=False,
    )

    op.alter_column(
        "members",
        "status",
        nullable=False,
    )

    # Replace the old unique constraint on user_id
    # with the explicitly indexed model definition.
    op.drop_constraint(
        op.f("members_user_id_key"),
        "members",
        type_="unique",
    )

    # Indexes.
    op.create_index(
        op.f("ix_members_first_name"),
        "members",
        ["first_name"],
        unique=False,
    )

    op.create_index(
        op.f("ix_members_last_name"),
        "members",
        ["last_name"],
        unique=False,
    )

    op.create_index(
        op.f("ix_members_position"),
        "members",
        ["position"],
        unique=False,
    )

    op.create_index(
        op.f("ix_members_slug"),
        "members",
        ["slug"],
        unique=True,
    )

    op.create_index(
        op.f("ix_members_status"),
        "members",
        ["status"],
        unique=False,
    )

    op.create_index(
        op.f("ix_members_user_id"),
        "members",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade the members table."""

    op.drop_index(
        op.f("ix_members_user_id"),
        table_name="members",
    )

    op.drop_index(
        op.f("ix_members_status"),
        table_name="members",
    )

    op.drop_index(
        op.f("ix_members_slug"),
        table_name="members",
    )

    op.drop_index(
        op.f("ix_members_position"),
        table_name="members",
    )

    op.drop_index(
        op.f("ix_members_last_name"),
        table_name="members",
    )

    op.drop_index(
        op.f("ix_members_first_name"),
        table_name="members",
    )

    op.drop_column(
        "members",
        "status",
    )

    op.drop_column(
        "members",
        "position",
    )

    op.drop_column(
        "members",
        "slug",
    )

    op.create_unique_constraint(
        op.f("members_user_id_key"),
        "members",
        ["user_id"],
    )

    sa.Enum(
        "ACTIVE",
        "INACTIVE",
        "ARCHIVED",
        name="member_status",
    ).drop(
        op.get_bind(),
        checkfirst=True,
    )