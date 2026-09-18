import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Drop all tables except 'sqlite_sequence'
for table_name in tables:
    table = table_name[0]
    if table != 'sqlite_sequence':
        cursor.execute(f'DROP TABLE IF EXISTS "{table}";')

conn.commit()
conn.close()
