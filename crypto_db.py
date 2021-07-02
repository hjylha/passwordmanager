import db
import crypto_stuff

# encrypt and add to database
def add_master_table(username, master_pw, fernet_thing):
    pw_encrypted = crypto_stuff.encrypt_text(master_pw, master_pw, fernet_thing)
    un_encrypted = crypto_stuff.encrypt_text(username, master_pw, fernet_thing)
    db.add_to_master_table(un_encrypted, pw_encrypted)

# this does not check if we add duplicates
def add_info(info, master_pw, fernet_thing):
    info_encrypted = crypto_stuff.encrypt_text_list(info, master_pw, fernet_thing)
    db.add_to_info_table(info_encrypted)


# get from database and decrypt
def get_master_table(master_pw, fernet_thing):
    master_e = db.get_master_table()
    master = crypto_stuff.decrypt_text_list(master_e, master_pw, fernet_thing)
    return master

def get_info_decrypted_w_rowid(master_pw, fernet_thing):
    results_e = db.get_info_w_rowid()
    results = []
    for result in results_e:
        result_d = crypto_stuff.decrypt_text_list(result[1:], master_pw, fernet_thing)
        # insert rowid to the start
        result_d.insert(0, result[0])
        results.append(result_d)
    return results

# find app_name from database (match ignoring capitalization)
def get_info_for_exact_app(app_name, master_pw, fernet_thing):
    results_e = db.get_info()
    results = []
    for result in results_e:
        result_d = crypto_stuff.decrypt_text_list(result, master_pw, fernet_thing)
        if result_d[3].lower() == app_name.lower():
            results.append(result_d)
    return results

# find app_name from database (apps whose name contains app_name)
# info = (username, email, pw, app, url)
def get_info_for_app(app_name, master_pw, fernet_thing):
    results_e = db.get_info()
    results = []
    for result in results_e:
        result_d = crypto_stuff.decrypt_text_list(result, master_pw, fernet_thing)
        if result_d[3].lower().find(app_name.lower()) > -1:
            results.append(result_d)
    return results

# same as above, but with rowid included
# info = (rowid, username, email, pw, app, url)
def get_info_for_app_w_rowid(app_name, master_pw, fernet_thing):
    results_e = db.get_info_w_rowid()
    results = []
    for result in results_e:
        # rowid is not encrypted, so ignore result[0]
        result_d = crypto_stuff.decrypt_text_list(result[1:], master_pw, fernet_thing)
        if result_d[3].lower().find(app_name.lower()) > -1:
            # add rowid back
            result_d.insert(0, result[0])
            results.append(result_d)
    return results

# create a list of apps in database
def get_app_list(master_pw, fernet_thing):
    app_list = []
    data = get_info_decrypted_w_rowid(master_pw, fernet_thing)
    for row in data:
        is_new = True
        # check for repeats
        for app in app_list:
            if app.lower() == row[4].lower():
                is_new = False
                break
        if is_new:
            app_list.append(row[4])
    return app_list

# change the password stored in row rowid
def change_pw_in_row(rowid, new_pw, master_pw, fernet_thing):
    new_pw_e = crypto_stuff.encrypt_text(new_pw, master_pw, fernet_thing)
    db.modify_password_by_rowid(rowid, new_pw_e)

# check if app name and username are in database
# info = (username, email, app, url)
def is_info_in_db(info, master_pw, fernet_thing):
    possible_rows = get_info_for_exact_app(info[2], master_pw, fernet_thing)
    if possible_rows == []:
        return False
    for row in possible_rows:
        if row[0] == info[0]:
            return True
    return False
