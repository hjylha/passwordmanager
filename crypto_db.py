import db
import crypto_stuff


def get_info_for_app(app_name, password, fernet_thing):
    results_e = db.get_info()
    results = []
    for result in results_e:
        result_d = crypto_stuff.decrypt_text_list(result, password, fernet_thing)
        if result_d[3].lower() == app_name.lower():
            results.append(result_d)
    return results

def print_app_list(password, fernet_thing):
    app_list_e = db.get_app_list()
    app_list = crypto_stuff.decrypt_text_list(app_list_e, password, fernet_thing)
    for app in app_list:
        print("\t", app)
