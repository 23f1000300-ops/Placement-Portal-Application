import sqlite3

def initialize_database():
    conn = sqlite3.connect("placement.db")
    cur = conn.cursor()

    # ================= USER BLOCK STATUS =================
    try:
        cur.execute("ALTER TABLE users ADD COLUMN is_blocked INTEGER DEFAULT 0")
    except:
        pass

    # ================= USERS =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # ================= COMPANIES =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS companies(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        status TEXT DEFAULT 'pending'
    )
    """)

    try:
        cur.execute("ALTER TABLE companies ADD COLUMN hr_contact TEXT")
    except:
        pass

    try:
        cur.execute("ALTER TABLE companies ADD COLUMN website TEXT")
    except:
        pass

    try:
        cur.execute("ALTER TABLE companies ADD COLUMN description TEXT")
    except:
        pass

    # ================= STUDENTS =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        resume TEXT
    )
    """)

    try:
        cur.execute("ALTER TABLE students ADD COLUMN contact_number TEXT")
    except:
        pass

    # ================= DRIVES =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS drives(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER,
        title TEXT,
        description TEXT,
        status TEXT DEFAULT 'pending'
    )
    """)
    
    try:
        cur.execute("ALTER TABLE drives ADD COLUMN eligibility TEXT")
    except:
        pass

    try:
        cur.execute("ALTER TABLE drives ADD COLUMN deadline TEXT")
    except:
        pass

    try:
        cur.execute("ALTER TABLE drives ADD COLUMN location TEXT")
    except:
        pass

    try:
        cur.execute("ALTER TABLE drives ADD COLUMN salary TEXT")
    except:
        pass

    # ================= APPLICATIONS =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS applications(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        job_id INTEGER,
        status TEXT DEFAULT 'applied'
    )
    """)

    try:
        cur.execute("ALTER TABLE applications ADD COLUMN drive_id INTEGER")
    except:
        pass

    try:
        cur.execute("ALTER TABLE applications ADD COLUMN application_date TEXT")
    except:
        pass

    try:
        cur.execute("ALTER TABLE applications ADD COLUMN remarks TEXT")
    except:
        pass


    # ================= DEFAULT ADMIN =================
    import hashlib

    hashed_admin = hashlib.sha256("admin".encode()).hexdigest()

    cur.execute("""
    INSERT OR IGNORE INTO users(id, email, password, role)
    VALUES(1, 'admin@gmail.com', ?, 'admin')
    """, (hashed_admin,))

    conn.commit()
    conn.close()