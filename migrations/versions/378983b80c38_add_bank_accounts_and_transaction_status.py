"""Add bank accounts and transaction status

Revision ID: 378983b80c38
Revises: 24e9c1c254e1
Create Date: [timestamp]

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '378983b80c38'
down_revision = '24e9c1c254e1'
branch_labels = None
depends_on = None


def upgrade():
    # Create bank_account table first
    op.create_table('bank_account',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bank_name', sa.String(length=100), nullable=False),
        sa.Column('account_number', sa.String(length=20), nullable=False),
        sa.Column('account_name', sa.String(length=200), nullable=True),
        sa.Column('initial_balance', sa.Float(), nullable=True),
        sa.Column('current_balance', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_bank_account_user'),
        sa.PrimaryKeyConstraint('id')
    )

    # Update transaction table
    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('transaction_time', sa.Time(), nullable=True))
        batch_op.add_column(sa.Column('completed_date', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('source', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('bank_account_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_transaction_bank_account', 'bank_account', ['bank_account_id'], ['id'])

    # Update import_history table
    with op.batch_alter_table('import_history', schema=None) as batch_op:
        batch_op.add_column(sa.Column('bank_account_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_import_history_bank_account', 'bank_account', ['bank_account_id'], ['id'])

    # Set default values
    op.execute("UPDATE transaction SET status = 'completed' WHERE status IS NULL")
    op.execute("UPDATE transaction SET source = 'manual' WHERE source IS NULL")
    # สำหรับ transaction ที่ import มา ให้ set status เป็น completed
    op.execute("UPDATE transaction SET status = 'completed', source = 'import' WHERE import_batch_id IS NOT NULL")


def downgrade():
    # Drop constraints first
    with op.batch_alter_table('import_history', schema=None) as batch_op:
        batch_op.drop_constraint('fk_import_history_bank_account', type_='foreignkey')
        batch_op.drop_column('bank_account_id')

    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.drop_constraint('fk_transaction_bank_account', type_='foreignkey')
        batch_op.drop_column('bank_account_id')
        batch_op.drop_column('source')
        batch_op.drop_column('completed_date')
        batch_op.drop_column('transaction_time')
        batch_op.drop_column('status')

    # Drop bank_account table
    op.drop_table('bank_account')