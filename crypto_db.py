import db
import crypto_stuff

# encrypt and add to database
def add_master_table(username, password, fernet_thing):
    pw_encrypted = crypto_stuff.encrypt_text(password, password, fernet_thing)
    un_encrypted = crypto_stuff.encrypt_text(username, password, fernet_thing)
    db.add_to_master_table(un_encrypted, pw_encrypted)

# TODO: this needs to check that there is no duplicates
def add_info(info, password, fernet_thing):
    info_encrypted = crypto_stuff.encrypt_text_list(info, password, fernet_thing)
    db.add_to_info_table(info_encrypted)
    app_list = get_app_list(password, fernet_thing)
    # let's not worry about lower/uppercase
    app_list_l = [app.lower() for app in app_list]
    # app_name is info[3]
    if not(info[3].lower() in app_list_l):
        db.add_to_apps_table(info_encrypted[3])


# get from database and decrypt
def get_master_table(password, fernet_thing):
    master_e = db.get_master_table()
    master = crypto_stuff.decrypt_text_list(master_e, password, fernet_thing)
    return master

def get_info_for_app(app_name, password, fernet_thing):
    results_e = db.get_info()
    results = []
    for result in results_e:
        result_d = crypto_stuff.decrypt_text_list(result, password, fernet_thing)
        if result_d[3].lower() == app_name.lower():
            results.append(result_d)
    return results

# info = (rowid, username, pw, email, app, url)
def get_info_for_app_w_rowid(app_name, password, fernet_thing):
    results_e = db.get_info_w_rowid()
    results = []
    for result in results_e:
        result_d = crypto_stuff.decrypt_text_list(result, password, fernet_thing)
        # app_name is index 4 now
        if result_d[4].lower() == app_name.lower():
            results.append(result_d)
    return results

def get_app_list(password, fernet_thing):
    app_list_e = db.get_app_list()
    app_list = crypto_stuff.decrypt_text_list(app_list_e, password, fernet_thing)
    return app_list
    # for app in app_list:
    #     print("\t", app)

# change the password stored in row rowid
def change_pw_in_row(rowid, new_pw, password, fernet_thing):
    new_pw_e = crypto_stuff.encrypt_text(new_pw, password, fernet_thing)
    db.modify_password_by_rowid(rowid, new_pw_e)
