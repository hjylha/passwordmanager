import db
import crypto_stuff

# encrypt and add to database
def add_master_table(username, password, fernet_thing):
    pw_encrypted = crypto_stuff.encrypt_text(password, password, fernet_thing)
    un_encrypted = crypto_stuff.encrypt_text(username, password, fernet_thing)
    db.add_to_master_table(un_encrypted, pw_encrypted)

def add_info(info, password, fernet_thing):
    info_encrypted = crypto_stuff.encrypt_text_list(info, password, fernet_thing)
    db.add_to_info_table(info_encrypted)
    app_list = get_app_list(password, fernet_thing)
    # app_name is info[3]
    if not(info[3] in app_list):
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

def get_app_list(password, fernet_thing):
    app_list_e = db.get_app_list()
    app_list = crypto_stuff.decrypt_text_list(app_list_e, password, fernet_thing)
    return app_list
    # for app in app_list:
    #     print("\t", app)
