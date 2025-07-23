import sqlite3

DB_NAME = "contacts.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Contact (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phoneNumber TEXT,
            email TEXT,
            linkedId INTEGER,
            linkPrecedence TEXT CHECK(linkPrecedence IN ('secondary', 'primary')),
            createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
            updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
            deletedAt DATETIME,
            FOREIGN KEY (linkedId) REFERENCES Contact (id)
        )
    ''')
    conn.commit()
    
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row 
    return conn

def execute_query(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if not params:
        cursor.execute(query)
    else:
        cursor.execute(query, params)
    
    if query.strip().upper().startswith('SELECT'):
        results = cursor.fetchall()
        conn.close()
        return [dict(row) for row in results]
    else:
        result_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return result_id

def close_db():
    pass