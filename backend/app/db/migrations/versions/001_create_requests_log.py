"""Create requests_log table."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_create_requests_log"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

provider_enum = postgresql.ENUM("openai", "anthropic", name="provider_enum", create_type=False)
request_status_enum = postgresql.ENUM(
    "success", "error", "blocked", name="request_status_enum", create_type=False
)


def upgrade() -> None:
    provider_enum.create(op.get_bind(), checkfirst=True)
    request_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "requests_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("client_id", sa.String(255), nullable=True),
        sa.Column("provider", provider_enum, nullable=False),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column("status", request_status_enum, nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("requests_log")
    request_status_enum.drop(op.get_bind(), checkfirst=True)
    provider_enum.drop(op.get_bind(), checkfirst=True)
