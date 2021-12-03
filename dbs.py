import time

from cryptography.fernet import Fernet

from db_setup import table_data, type_tuples
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
    
# generating many rows of dummy data
def generate_dummy_data(type_tuple, num_of_rows, fernet_obj=None, password_hasher=None):
    dummy_data = []
    for _ in range(num_of_rows):
        datarow = tuple(generate_dummy_string(t, fernet_obj, password_hasher) for t in type_tuple)
        dummy_data.append(datarow)
    return dummy_data


# initiate 'auth', 'keys' or 'password' db
def initiate_db(filepath, db_type, num_of_dummy_inserts=10):
    db = DB_general(filepath)
    for name, table_dict in table_data.items():
        if name == db_type:
            tables = table_dict
            type_tuple = type_tuples[name]
            break
    else:
        raise Exception('Invalid db type')

    # create tables
    for table, column_data in tables.items():
        db.create_table(table, column_data)
    
    # insert dummy data to tables
    ph = cs.PasswordHasher() if 'hash' in type_tuple else None
    f = cs.Fernet(cs.Fernet.generate_key()) if 'key' in type_tuple else None
    
    for table, column_data in tables.items():
        t_tuple = type_tuple[:len(column_data.keys())]
        dummy_data = generate_dummy_data(t_tuple, num_of_dummy_inserts, f, ph)
        db.insert_many(table, column_data.keys(), dummy_data)
    return db
    





