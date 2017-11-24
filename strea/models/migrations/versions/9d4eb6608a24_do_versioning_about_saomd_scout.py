"""Do versioning about SAOMD Scout

Revision ID: 9d4eb6608a24
Revises: c3b5d97707c4
Create Date: 2017-11-25 00:36:17.837358

"""

from alembic import op

import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d4eb6608a24'
down_revision = 'c3b5d97707c4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'saomd_scout',
        sa.Column(
            'version',
            sa.Integer(),
            default=1,
            server_default='1',
            nullable=False
        )
    )


def downgrade():
    op.drop_column('saomd_scout', 'version')
