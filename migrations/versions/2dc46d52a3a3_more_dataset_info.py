"""more dataset info

Revision ID: 2dc46d52a3a3
Revises: 96052cfeea9b
Create Date: 2020-07-16 22:22:14.387304

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2dc46d52a3a3'
down_revision = '96052cfeea9b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('dataset', sa.Column('name', sa.String(length=128), nullable=True))
    op.add_column('dataset', sa.Column('path', sa.String(length=240), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('dataset', 'path')
    op.drop_column('dataset', 'name')
    # ### end Alembic commands ###
