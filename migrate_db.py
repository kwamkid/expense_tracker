import sqlite3

# Connect to database
conn = sqlite3.connect('instance/expense_tracker.db')
cursor = conn.cursor()

# Create bank_account table
cursor.execute('''
CREATE TABLE IF NOT EXISTS bank_account (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_name VARCHAR(100) NOT NULL,
    account_number VARCHAR(20) NOT NULL,
    account_name VARCHAR(200),
    initial_balance FLOAT DEFAULT 0,
    current_balance FLOAT DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id)
)
''')

# Add columns to transaction table
try:
    cursor.execute('ALTER TABLE "transaction" ADD COLUMN status VARCHAR(20) DEFAULT "pending"')
except sqlite3.OperationalError:
    print("Column status already exists")

try:
    cursor.execute('ALTER TABLE "transaction" ADD COLUMN transaction_time TIME')
except sqlite3.OperationalError:
    print("Column transaction_time already exists")

try:
    cursor.execute('ALTER TABLE "transaction" ADD COLUMN completed_date DATETIME')
except sqlite3.OperationalError:
    print("Column completed_date already exists")

try:
    cursor.execute('ALTER TABLE "transaction" ADD COLUMN source VARCHAR(20) DEFAULT "manual"')
except sqlite3.OperationalError:
    print("Column source already exists")

try:
    cursor.execute('ALTER TABLE "transaction" ADD COLUMN bank_account_id INTEGER REFERENCES bank_account(id)')
except sqlite3.OperationalError:
    print("Column bank_account_id already exists")

# Add column to import_history
try:
    cursor.execute('ALTER TABLE import_history ADD COLUMN bank_account_id INTEGER REFERENCES bank_account(id)')
except sqlite3.OperationalError:
    print("Column bank_account_id already exists")

# Update existing transactions
cursor.execute('UPDATE "transaction" SET status = "completed" WHERE status IS NULL')
cursor.execute('UPDATE "transaction" SET source = "import" WHERE import_batch_id IS NOT NULL')
cursor.execute('UPDATE "transaction" SET source = "manual" WHERE source IS NULL')

conn.commit()
conn.close()

print("Migration completed successfully!")