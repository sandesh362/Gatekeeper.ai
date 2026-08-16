"""Create detection_results table."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_create_detection_results"
down_revision: Union[str, None] = "001_create_requests_log"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

detection_decision_enum = postgresql.ENUM(
    "PASS", "FLAG", "BLOCK", name="detection_decision_enum", create_type=False
)


def upgrade() -> None:
    detection_decision_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "detection_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("requests_log.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("decision", detection_decision_enum, nullable=False),
        sa.Column("layer_breakdown", postgresql.JSONB(), nullable=False),
        sa.Column("canary_triggered", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("reasoning_summary", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("detection_results")
    detection_decision_enum.drop(op.get_bind(), checkfirst=True)
