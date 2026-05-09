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
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE sale_status AS ENUM ('pending_payment', 'completed', 'cancelled');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS sales (
            id UUID NOT NULL,
            vehicle_id VARCHAR NOT NULL,
            vehicle_price_at_sale NUMERIC(12, 2) NOT NULL,
            buyer_cpf VARCHAR(14) NOT NULL,
            sale_date DATE NOT NULL,
            payment_code UUID NOT NULL,
            status sale_status NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            CONSTRAINT pk_sales PRIMARY KEY (id),
            CONSTRAINT uq_sales_payment_code UNIQUE (payment_code)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_sales_status ON sales (status)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_sales_vehicle_price_at_sale ON sales (vehicle_price_at_sale)"
    )


def downgrade() -> None:
    op.drop_index("ix_sales_vehicle_price_at_sale", table_name="sales")
    op.drop_index("ix_sales_status", table_name="sales")
    op.drop_table("sales")
    sa.Enum(name="sale_status").drop(op.get_bind(), checkfirst=True)
