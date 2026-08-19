"""Add organizations, users, API keys, and request tenant references."""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_add_multitenancy_auth"
down_revision: Union[str, None] = "002_create_detection_results"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table("organizations", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("name", sa.String(255), nullable=False), sa.Column("plan", sa.String(32), nullable=False, server_default="free"), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_table("api_keys", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False), sa.Column("key_hash", sa.String(64), nullable=False, unique=True), sa.Column("key_prefix", sa.String(16), nullable=False), sa.Column("name", sa.String(255), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("last_used_at", sa.DateTime(timezone=True)), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("rate_limit_per_minute", sa.Integer(), nullable=False, server_default="60"))
    op.create_table("dashboard_users", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False), sa.Column("email", sa.String(320), nullable=False, unique=True), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("role", sa.String(32), nullable=False, server_default="admin"))
    op.add_column("requests_log", sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("requests_log", sa.Column("api_key_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_requests_org", "requests_log", "organizations", ["organization_id"], ["id"])
    op.create_foreign_key("fk_requests_key", "requests_log", "api_keys", ["api_key_id"], ["id"])
    op.add_column("detection_results", sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_detection_org", "detection_results", "organizations", ["organization_id"], ["id"])
    # Existing pre-Phase-6 records remain unassigned; new records are tenant-scoped.
    op.drop_column("requests_log", "client_id")

def downgrade() -> None:
    op.add_column("requests_log", sa.Column("client_id", sa.String(255), nullable=True))
    op.drop_constraint("fk_detection_org", "detection_results", type_="foreignkey"); op.drop_column("detection_results", "organization_id")
    op.drop_constraint("fk_requests_key", "requests_log", type_="foreignkey"); op.drop_constraint("fk_requests_org", "requests_log", type_="foreignkey"); op.drop_column("requests_log", "api_key_id"); op.drop_column("requests_log", "organization_id")
    op.drop_table("dashboard_users"); op.drop_table("api_keys"); op.drop_table("organizations")
