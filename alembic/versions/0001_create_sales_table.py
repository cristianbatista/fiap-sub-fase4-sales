"""create sales table

Revision ID: 0001
Revises:
Create Date: 2026-05-09

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    sale_status = sa.Enum(
        "pending_payment",
        "completed",
        "cancelled",
        name="sale_status",
    )
    sale_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "sales",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("vehicle_id", sa.String(), nullable=False),
        sa.Column("vehicle_price_at_sale", sa.Numeric(12, 2), nullable=False),
        sa.Column("buyer_cpf", sa.String(14), nullable=False),
        sa.Column("sale_date", sa.Date(), nullable=False),
        sa.Column("payment_code", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending_payment",
                "completed",
                "cancelled",
                name="sale_status",
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payment_code", name="uq_sales_payment_code"),
    )
    op.create_index("ix_sales_status", "sales", ["status"])
    op.create_index(
        "ix_sales_vehicle_price_at_sale", "sales", ["vehicle_price_at_sale"]
    )


def downgrade() -> None:
    op.drop_index("ix_sales_vehicle_price_at_sale", table_name="sales")
    op.drop_index("ix_sales_status", table_name="sales")
    op.drop_table("sales")
    sa.Enum(name="sale_status").drop(op.get_bind(), checkfirst=True)
