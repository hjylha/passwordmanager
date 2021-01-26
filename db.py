import sqlite3

"""
conn = sqlite3.connect("pw.db")
c = conn.cursor()
c.execute()
conn.commit()
conn.close()
"""

# create the tables
# should the names be encrypted as well?
def create_info_table():
    conn = sqlite3.connect("pw.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE info (
        username TEXT,
        email TEXT,
        password TEXT,
        app_name TEXT,
        url TEXT
    )    
        """)
    conn.commit()
    conn.close()
    print("Information table added to the database")

def create_app_list():
    conn = sqlite3.connect("pw.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE apps (
        app_name TEXT
    ) """)
    conn.commit()
    conn.close()
    print("App list table added to the database")

def create_master_table():
    conn = sqlite3.connect("pw.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE master (
        master_name TEXT,
        master_password TEXT
    ) """)
    conn.commit()
    conn.close()
    print("Master table added to the database")

def create_db():
    create_master_table()
    create_info_table()
    create_app_list()


# reset the database
# maybe not necessary, just remove the db file instead
def reset_db():
    conn = sqlite3.connect("pw.db")
    c = conn.cursor()
    try:
        c.execute("DROP TABLE info")
    except sqlite3.OperationalError:
        print("Table 'info' does not exist")
    try:
        c.execute("DROP TABLE master")
    except sqlite3.OperationalError:
        print("Table 'master' does not exist")
    try:
        c.execute("DROP TABLE apps")
    except sqlite3.OperationalError:
        print("Table 'apps' does not exist")
    conn.commit()
    print("Tables dropped from the database")
    conn.close()
    create_db()


# Add stuff to the database
# encryption comes into play at some point, so print statement probably fails
def add_to_master_table(name, password):
    # make sure these don't already exist
    info = get_master_table()
    if info == None:
        conn = sqlite3.connect("pw.db")
        c = conn.cursor()
        c.execute("INSERT INTO master VALUES (?, ?)", (name, password))
        conn.commit()
        conn.close()
        print("Master password for user " + name + " has been added to the database")
        return 0
    else:
        print("Database already has a master password")
        return -1

# info = (username, email, password, app_name, url)
def add_to_info_table(info):
    conn = sqlite3.connect("pw.db")
    c = conn.cursor()
    c.execute("INSERT INTO info VALUES (?, ?, ?, ?, ?)", info)
    
    # search = f"SELECT app_name FROM apps WHERE app_name LIKE {info[3]}"
    search = "SELECT app_name FROM apps"
    c.execute(search)
    names = c.fetchall()
    # if names == []:
    if not(info[3] in names):
        c.execute("INSERT INTO apps VALUES (?)", [info[3]])
        # c.execute("INSERT INTO apps VALUES (?, ?)", (info[3], 'nonsense'))
    else:
        print(info[3], "is already in database")
    conn.commit()
    conn.close()
    print("Password to " + info[3] + " for user " + info[0] + " has been added to the database")
    return 0


# funtions to retrieve stuff from the database
def get_master_table():
    conn = sqlite3.connect("pw.db")
    c = conn.cursor()
    c.execute("SELECT * FROM master")
    master = c.fetchone()
    conn.close()
    return master

def get_app_list():
    conn = sqlite3.connect("pw.db")
    c = conn.cursor()
    c.execute("SELECT * FROM apps")
    app_list = c.fetchall()
    conn.close()
    return app_list

def get_password_to_app(app):
    conn = sqlite3.connect("pw.db")
    c = conn.cursor()
    command = "SELECT * FROM info WHERE app_name LIKE ?"
    c.execute(command, [app])
    entries = c.fetchall()
    conn.close()
    return entries

