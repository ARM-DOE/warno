"""updated user model for login

Revision ID: 20e5e62c8a86
Revises: 30115ede2fc7
Create Date: 2016-07-25 17:39:43.471773

"""

# revision identifiers, used by Alembic.
revision = '20e5e62c8a86'
down_revision = '30115ede2fc7'

from sqlalchemy.orm.session import Session
from alembic import op
import sqlalchemy as sa


# Default each User's username to the string version of their user_id, guaranteeing the name is unique
# because the id is a primary key (therefore unique).  The usernames can then be manually changed in the database.
def default_username_if_empty(session):
    for entry in session.execute("SELECT user_id from users").fetchall():
        session.execute("UPDATE users SET username = :username WHERE user_id = :entry_id",
                        dict(entry_id=entry[0], username=str(entry[0])))
        session.commit()


def upgrade():
    op.add_column('users', sa.Column('confirmed_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('email', sa.String(), nullable=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('reset_password_token', sa.String(length=100), server_default='', nullable=False))
    op.add_column('users', sa.Column('username', sa.String(), nullable=False, server_default=''))
    op.alter_column('users', 'password',
                    existing_type=sa.VARCHAR(),
                    nullable=False)
    session = Session(bind=op.get_bind())
    default_username_if_empty(session)
    op.create_unique_constraint('users_username_key', 'users', ['username'])
    op.drop_column('users', 'e-mail')


def downgrade():
    op.add_column('users', sa.Column('e-mail', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint('users_username_key', 'users', type_='unique')
    op.alter_column('users', 'password',
                    existing_type=sa.VARCHAR(),
                    nullable=True)
    op.drop_column('users', 'username')
    op.drop_column('users', 'reset_password_token')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'email')
    op.drop_column('users', 'confirmed_at')
