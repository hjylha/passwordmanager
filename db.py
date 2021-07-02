import sqlite3
from pm_data import default_db_filename

# conn = sqlite3.connect("pw.db")
# conn = connect_to_db()
# c = conn.cursor()
# c.execute()
# conn.commit()
# conn.close()

# default_db_filename = "pw.db"

def connect_to_db(db_filename=default_db_filename):
    return sqlite3.connect(db_filename)

# create the tables
# should the names be encrypted as well?
def create_info_table(db_filename=default_db_filename):
    conn = connect_to_db(db_filename)
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

def create_app_list(db_filename=default_db_filename):
    conn = connect_to_db(db_filename)
    c = conn.cursor()
    c.execute("""CREATE TABLE apps (
        app_name TEXT,
        blah TEXT
    ) """)
    conn.commit()
    conn.close()
    print("App list table added to the database")

def create_master_table(db_filename=default_db_filename):
    conn = connect_to_db(db_filename)
    c = conn.cursor()
    c.execute("""CREATE TABLE master (
        master_name TEXT,
        master_password TEXT
    ) """)
    conn.commit()
    conn.close()
    print("Master table added to the database")

def create_db(db_filename=default_db_filename):
    create_master_table(db_filename)
    create_info_table(db_filename)
    create_app_list(db_filename)


# reset the database
# maybe not necessary, just remove the db file instead
def reset_db(db_filename=default_db_filename):
    conn = connect_to_db(db_filename)
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
    create_db(db_filename)


# Add stuff to the database
# encryption comes into play at some point, so print statement probably fails
def add_to_master_table(name, password, db_filename=default_db_filename):
    # make sure these don't already exist
    info = get_master_table(db_filename)
    if info == None:
        conn = connect_to_db(db_filename)
        c = conn.cursor()
        c.execute("INSERT INTO master VALUES (?, ?)", (name, password))
        conn.commit()
        conn.close()
        # print("Master password for user " + name + " has been added to the database")
        return 0
    else:
        print("Database already has a master password")
        return -1

# info = (username, email, password, app_name, url)
def add_to_info_table(info, db_filename=default_db_filename):
    conn = connect_to_db(db_filename)
    c = conn.cursor()
    c.execute("INSERT INTO info VALUES (?, ?, ?, ?, ?)", info)
    
    # # search = f"SELECT app_name FROM apps WHERE app_name LIKE {info[3]}"
    # search = "SELECT app_name FROM apps"
    # c.execute(search)
    # names = c.fetchall()
    # if not(info[3] in [name[0] for name in names]):
    #     # c.execute("INSERT INTO apps VALUES (?)", [info[3]])
    #     c.execute("INSERT INTO apps VALUES (?, ?)", (info[3], 'nah'))
    # else:
    #     print(info[3], "is already in database")
    conn.commit()
    conn.close()
    # print("Password to " + info[3] + " for user " + info[0] + " has been added to the database")
    return 0

def add_to_apps_table(app_name, db_filename=default_db_filename):
    conn = connect_to_db(db_filename)
    c = conn.cursor()
    c.execute("INSERT INTO apps VALUES (?, ?)", (app_name, 'nah'))
    conn.commit()
    conn.close()


# funtions to retrieve stuff from the database
def get_master_table(db_filename=default_db_filename):
    conn = connect_to_db(db_filename)
    c = conn.cursor()
    c.execute("SELECT * FROM master")
    master = c.fetchone()
    conn.close()
    return master

def get_app_list(db_filename=default_db_filename):
    conn = connect_to_db(db_filename)
    c = conn.cursor()
    c.execute("SELECT * FROM apps")
    app_list = c.fetchall()
    conn.close()
    return [app_entry[0] for app_entry in app_list]

'''
def get_password_to_app(app, db_filename=default_db_filename):
    conn = connect_to_db(db_filename)
    c = conn.cursor()
    command = "SELECT * FROM info WHERE app_name LIKE ?"
    c.execute(command, [app])
    entries = c.fetchall()
    conn.close()
    return entries
    '''

def get_info(db_filename=default_db_filename):
    conn = connect_to_db(db_filename)
    c = conn.cursor()
    c.execute("SELECT * FROM info")
    all_info = c.fetchall()
    conn.close()
    return all_info

def get_info_w_rowid(db_filename=default_db_filename):
    conn = connect_to_db(db_filename)
    c = conn.cursor()
    c.execute("SELECT rowid, * FROM info")
    all_info = c.fetchall()
    conn.close()
    return all_info


# modify password on a specific row
def modify_password_by_rowid(rowid, new_password, db_filename=default_db_filename):
    conn = connect_to_db(db_filename)
    c = conn.cursor()
    c.execute("UPDATE info SET password = ? WHERE rowid = ?", (new_password, rowid))
    conn.commit()
    conn.close()


def show_everything(db_filename=default_db_filename):
    conn = connect_to_db(db_filename)
    c = conn.cursor()
    c.execute("SELECT * FROM master")
    header = c.fetchall()
    c.execute("SELECT * FROM info")
    info_table = c.fetchall()
    c.execute("SELECT * FROM apps")
    app_list = c.fetchall()
    conn.close()
    print("\nContents of table 'master'")
    for head in header:
        print(head)
    print("\nContents of table 'apps")
    for app_item in app_list:
        print(app_item)
    print("\nContents of table 'info'")
    for item in info_table:
        print(item)

# check if database has a username and password
def check_db(db_filename=default_db_filename):
    try:
        master = get_master_table(db_filename)
    except sqlite3.OperationalError:
        return False
    if master == None:
        return False
    return True

# only used for testing, at least for now
def delete_row(rowid, db_filename=default_db_filename):
    conn = connect_to_db(db_filename)
    c = conn.cursor()
    # here rowid needs to be string for some reason
    c.execute("DELETE from info WHERE rowid = ?", str(rowid))
    conn.commit()
    conn.close()