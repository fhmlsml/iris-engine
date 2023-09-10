"""delete user cascade

Revision ID: 92bf95eaf61c
Revises: 57af1ab69a17
Create Date: 2022-10-15 10:44:22.325746

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '92bf95eaf61c'
down_revision = '57af1ab69a17'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('maintainers_email_fkey', 'maintainers', type_='foreignkey')
    op.create_foreign_key(None, 'maintainers', 'users', ['email'], ['email'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'maintainers', type_='foreignkey')
    op.create_foreign_key('maintainers_email_fkey', 'maintainers', 'users', ['email'], ['email'])
    # ### end Alembic commands ###