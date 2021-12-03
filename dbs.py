import time

from db_setup import keys_table_data, data_db_table_data
from db_general import DB_general
import crypto_stuff as cs


# generate a dummy encrypted string, key or has
def generate_dummy_string(type_of_string, fernet_obj=None, password_hasher=None):
    if type_of_string == 'normal':
        if fernet_obj is None:
            fernet_obj = cs.Fernet(cs.Fernet.generate_key())
        return cs.encrypt_text(cs.generate_password(), fernet_obj)
    elif type_of_string == 'key':
        if fernet_obj is None:
            fernet_obj = cs.Fernet(cs.Fernet.generate_key())
        return fernet_obj.encrypt(cs.Fernet.generate_key())
    elif type_of_string == 'hash':
        if password_hasher is None:
            password_hasher = cs.PasswordHasher()
        return password_hasher.hash(cs.generate_password())
    else:
        raise Exception('Invalid type of dummy data')
    
    
def generate_dummy_data(type_tuple, num_of_rows, fernet_obj=None, password_hasher=None):
    dummy_data = []
    for _ in range(num_of_rows):
        datarow = tuple(generate_dummy_string(t, fernet_obj, password_hasher) for t in type_tuple)
        dummy_data.append(datarow)
    return dummy_data

def initiate_keys_db(filepath, num_of_dummy_inserts):
    dbk = DB_general(filepath)
    # create tables
    for table, column_data in keys_table_data.items():
        dbk.create_table(table, column_data)
    # insert dummy data
    auth_dummy_data = []
    ph = cs.PasswordHasher()
    for _ in range(num_of_dummy_inserts[0]):
        hash = ph.hash(cs.generate_password())
        key = cs.Fernet.generate_key()
    return dbk

def initiate_password_db(filepath, num_of_dummy_inserts):
    dbp = DB_general(filepath)
    # create tables
    for table, column_data in data_db_table_data.items():
        dbp.create_table(table, column_data)
    # insert dummy data
    return dbp


