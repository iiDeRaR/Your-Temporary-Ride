import sqlite3

def init_db():
    conn = sqlite3.connect('rental.db')
    cursor = conn.cursor()
    
   
    cursor.execute('''CREATE TABLE IF NOT EXISTS cars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model TEXT, year TEXT, plate_id TEXT UNIQUE, 
        status TEXT DEFAULT 'active', price_per_day REAL)''')
    
  
    cursor.execute('''CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE, email TEXT)''')
    
  
    cursor.execute('''CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT, car_id INTEGER, 
        start_date TEXT, end_date TEXT, 
        status TEXT DEFAULT 'Reserved', payment REAL DEFAULT 0)''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()