"""Init

Revision ID: 7e22341a0565
Revises: 
Create Date: 2025-05-08 09:00:53.591193

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e22341a0565'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('company',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=True),
    sa.Column('address', sa.Text(), nullable=True),
    sa.Column('tax_id', sa.String(length=20), nullable=True),
    sa.Column('logo_path', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('owner_id', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('line_id', sa.String(length=100), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=True),
    sa.Column('picture_url', sa.String(length=255), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('company_id', sa.Integer(), nullable=True),
    sa.Column('company_name', sa.String(length=200), nullable=True),
    sa.Column('company_address', sa.Text(), nullable=True),
    sa.Column('tax_id', sa.String(length=20), nullable=True),
    sa.Column('logo_path', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['company_id'], ['company.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('line_id')
    )
    op.create_table('bank_account',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('bank_name', sa.String(length=100), nullable=False),
    sa.Column('account_number', sa.String(length=20), nullable=False),
    sa.Column('account_name', sa.String(length=200), nullable=True),
    sa.Column('initial_balance', sa.Float(precision=2), nullable=True),
    sa.Column('current_balance', sa.Float(precision=2), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('company_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['company_id'], ['company.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('category',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('type', sa.String(length=10), nullable=False),
    sa.Column('keywords', sa.Text(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('company_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['company_id'], ['company.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('invite_token',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('token', sa.String(length=100), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('used', sa.Boolean(), nullable=True),
    sa.Column('used_by', sa.Integer(), nullable=True),
    sa.Column('company_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['company_id'], ['company.id'], ),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
    sa.ForeignKeyConstraint(['used_by'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token')
    )
    op.create_table('user_company',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('is_admin', sa.Boolean(), nullable=True),
    sa.Column('active_company', sa.Boolean(), nullable=True),
    sa.Column('joined_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['company_id'], ['company.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'company_id')
    )
    op.create_table('import_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('batch_id', sa.String(length=50), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('bank_type', sa.String(length=50), nullable=False),
    sa.Column('import_date', sa.DateTime(), nullable=True),
    sa.Column('transaction_count', sa.Integer(), nullable=True),
    sa.Column('total_amount', sa.Float(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('bank_account_id', sa.Integer(), nullable=True),
    sa.Column('company_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['bank_account_id'], ['bank_account.id'], ),
    sa.ForeignKeyConstraint(['company_id'], ['company.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('batch_id')
    )
    op.create_table('transaction',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('transaction_date', sa.Date(), nullable=False),
    sa.Column('type', sa.String(length=10), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('transaction_time', sa.Time(), nullable=True),
    sa.Column('completed_date', sa.DateTime(), nullable=True),
    sa.Column('source', sa.String(length=20), nullable=True),
    sa.Column('bank_account_id', sa.Integer(), nullable=True),
    sa.Column('bank_reference', sa.String(length=100), nullable=True),
    sa.Column('import_batch_id', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.Column('company_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['bank_account_id'], ['bank_account.id'], ),
    sa.ForeignKeyConstraint(['category_id'], ['category.id'], ),
    sa.ForeignKeyConstraint(['company_id'], ['company.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('transaction')
    op.drop_table('import_history')
    op.drop_table('user_company')
    op.drop_table('invite_token')
    op.drop_table('category')
    op.drop_table('bank_account')
    op.drop_table('user')
    op.drop_table('company')
    # ### end Alembic commands ###
