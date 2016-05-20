"""Added submit_log event code

Revision ID: 717007ed12a3
Revises: 78408cfddef6
Create Date: 2016-03-21 18:44:13.323871

"""

# revision identifiers, used by Alembic.
revision = '717007ed12a3'
down_revision = '78408cfddef6'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from sqlalchemy.sql import table, column
from alembic import op


def upgrade():
    # Creates an ad-hoc table for use with update and insert
    event_code_table = table('event_codes',
                       column('description', sa.String),
                       column('event_code', sa.Integer)
                       )
    connection = op.get_bind()
    # Update the event code 5 that used to be 'prosensing_paf' to 'instrument_log', then insert a new event code 6 'prosensing_paf'
    # Only runs if the table is not empty (set schema, blank database)
    result = connection.execute("SELECT event_code FROM event_codes LIMIT 1")

    if result.rowcount > 0:
        connection.execute(event_code_table.update().where(event_code_table.c.event_code == 5).values({'description': op.inline_literal('instrument_log')}))
        op.bulk_insert(event_code_table, [{'event_code': 6, 'description': 'prosensing_paf'}])


def downgrade():
    # Creates an ad-hoc table for use with update and delete
    event_code_table = table('event_codes',
                       column('description', sa.String),
                       column('event_code', sa.Integer)
                       )
    connection = op.get_bind()
    # Delete the event code 6 and replace the event code 5 with 'prosensing_paf'
    # Exact reverse of 'upgrade' function
    connection.execute(event_code_table.delete(event_code_table.c.event_code == 6))
    connection.execute(event_code_table.update().where(event_code_table.c.event_code == 5).values({'description': op.inline_literal('prosensing_paf')}))

