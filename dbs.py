import time

from cryptography.fernet import Fernet

from db_setup import table_data, type_tuples
from db_general import DB_general
import crypto_stuff as cs


# generate a dummy encrypted string, key or has
def generate_dummy_string(type_of_string, fernet_obj=None, password_hasher=None):
    if type_of_string == 'normal':
        if fernet_obj is None:
            fernet_obj = Fernet(Fernet.generate_key())
        return cs.encrypt_text(cs.generate_password(), fernet_obj)
    elif type_of_string == 'key':
        if fernet_obj is None:
            fernet_obj = Fernet(Fernet.generate_key())
        return fernet_obj.encrypt(Fernet.generate_key())
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
    

class DB_auth(DB_general):

    def __init__(self, filepath_of_db) -> None:
        super().__init__(filepath_of_db)
        self.table = 'auth'
        self.cols = ('hash', 'master_key', 'date_modified')
        self.length = len(self.select_all(self.table))
        # check that it contains the required stuff
        # TODO: maybe improve these
        if table_data[self.table][self.table] != self.tables[self.table]:
            raise Exception('No auth table in the database.')
        if len(self.select_all(self.table)[0]) != 4:
            raise Exception('Something is wrong with columns in auth table')

    def check_uniqueness_of_keys(self):
        keys = tuple(row[0] for row in self.select_columns(self.table, self.cols[1:]))
        if len(keys) == len(set(keys)):
            return True
        # if len(keys) != len(set(keys)):
        return False

    def is_key_in_keys(self, key):
        keys = tuple(row[0] for row in self.select_columns(self.table, self.cols[1:]))
        if key in keys:
            return True
        return False

    # check the given password and return the corresponding (encrypted) master key
    def check_password(self, password):
        content = self.select_columns(self.table, self.cols[:2])
        ph = cs.PasswordHasher()
        search_results = []
        for row in content:
            try:
                ph.verify(row[0], password)
                search_results.append(row[1])
            except cs.argon2.exceptions.VerifyMismatchError:
                pass
        if len(search_results) == 1:
            return search_results[0]
        # not sure what to do if password is in db multiple times
        if len(search_results) > 1:
            raise Exception('This password is in the database more than once.')
        if not search_results:
            raise Exception('Given password not in database.')
        
    # add password and hash it; generate key and time, and encrypt them
    def add_password(self, password, salt):
        # from pm_data import salt_thingie
        ph = cs.PasswordHasher()
        hash = ph.hash(password)
        f = cs.do_crypto_stuff(password, salt, 200_000)
        while True:
            master_key = Fernet.generate_key()
            encrypted_master_key = f.encrypt(master_key)
            if not self.is_key_in_keys(encrypted_master_key):
                encrypted_time = cs.encrypt_text(str(int(time.time())), f)
                datarow = (hash, encrypted_master_key, encrypted_time)
                rowid = cs.secrets.randbelow(self.length) + 1
                self.update_by_rowid(self.table, self.cols, datarow, rowid)
                break
    
    # get the actual master key
    def decrypt_key(self, encrypted_key, password, salt):
        f = cs.do_crypto_stuff(password, salt, 200_000)
        return f.decrypt(encrypted_key)


class DB_keys(DB_general):

    def __init__(self, filepath_of_db) -> None:
        super().__init__(filepath_of_db)
        self.table_tuple = ('app_keys', 'email_keys', 'data_keys')
        self.cols = ('key', 'in_use', 'date_modified')
    
    # find rows that are not in use (and also rows that are)
    def find_vacancies(self, table, master_key):
        vacant_rowids = []
        in_use_rowids = []
        f = Fernet(master_key)
        all_data = self.select_all(table)
        for row in all_data:
            in_use = cs.try_decrypt_wo_exceptions(row[2].encode(), f)
            if not in_use:
                vacant_rowids.append(row[0])
            elif in_use.decode() == 'in_use':
                in_use_rowids.append(row[0])
            else:
                vacant_rowids.append(row[0])
        return [vacant_rowids, in_use_rowids]

    # insert key to table, change row status to in_use and add timestamp
    def insert_key(self, key, table, rowid, master_key):
        f = Fernet(master_key)
        timestamp = str(int(time.time()))
        data = (f.encrypt(key), f.encrypt('in_use'.encode()).decode(), f.encrypt(timestamp.encode()).decode())
        self.update_by_rowid(table, self.cols, data, rowid)
    
    # generate new key and add it to table
    def add_new_key(self, table, master_key):
        available_rowids = self.find_vacancies(table, master_key)[0]
        rowid = cs.secrets.choice(available_rowids)
        key = Fernet.generate_key()
        self.insert_key(key, table, rowid, master_key)

    # get the actual key
    def decrypt_key(self, encrypted_key, master_key):
        return Fernet(master_key).decrypt(encrypted_key)


class DB_password(DB_general):

    def insert_data(self, data, fernet):
        pass




