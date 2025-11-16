import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

db_path = os.getenv('DB_PATH', 'db.sqlite')
conn = sqlite3.connect(db_path)
c = conn.cursor()

# User Profile table
c.execute('''
    CREATE TABLE IF NOT EXISTS UserProfile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        address TEXT,
        email TEXT,
        phone TEXT,
        IBAN TEXT,
        business_facts TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Submission table
c.execute('''
    CREATE TABLE IF NOT EXISTS Submission (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        userId INTEGER,
        intent TEXT,
        selected_forms TEXT,
        answers TEXT,
        files TEXT,
        status TEXT,
        audit_trail TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (userId) REFERENCES UserProfile(id)
    )
''')

# Form Templates table
c.execute('''
    CREATE TABLE IF NOT EXISTS FormTemplate (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        form_id TEXT UNIQUE,
        form_name TEXT,
        form_type TEXT,
        template_path TEXT,
        field_mappings TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Compliance Pack table
c.execute('''
    CREATE TABLE IF NOT EXISTS CompliancePack (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id INTEGER,
        pack_type TEXT,
        file_path TEXT,
        regulations TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (submission_id) REFERENCES Submission(id)
    )
''')

# Insert mock user profile
c.execute('''
    INSERT OR IGNORE INTO UserProfile (id, name, address, email, phone, business_facts)
    VALUES (1, 'Prime Bakery', 'Flensburg St 1, 24937 Flensburg', 'info@bakery.de', '+49 461 123456', 'Small bakery, 5 employees, uses electric ovens')
''')

conn.commit()
conn.close()
print(f"Database initialized at {db_path}")
