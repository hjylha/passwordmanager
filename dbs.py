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


class PasswordNotFoundError(Exception):
    pass
    

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
            raise PasswordNotFoundError('Given password not in database.')
        
    # add password and hash it; generate key if necessary; add time, and encrypt them
    def add_password(self, password, salt, master_key=None, rowid=None):
        # from pm_data import salt_thingie
        ph = cs.PasswordHasher()
        hash = ph.hash(password)
        f = cs.do_crypto_stuff(password, salt, 200_000)
        while True:
            if not master_key:
                master_key = Fernet.generate_key()
            encrypted_master_key = f.encrypt(master_key)
            if not self.is_key_in_keys(encrypted_master_key):
                encrypted_time = cs.encrypt_text(str(int(time.time())), f)
                datarow = (hash, encrypted_master_key, encrypted_time)
                if not rowid:
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
    
    # add more dummy data
    def add_dummy_data(self, table_num, num_of_rows=10):
        t_tuple = type_tuples['keys']
        f = Fernet(Fernet.generate_key())
        dummy_data = generate_dummy_data(t_tuple, num_of_rows, f)
        table = self.table_tuple[table_num]
        self.insert_many(table, self.tables[table].keys(), dummy_data)

    # find rows that are not in use (and also rows that are)
    def find_vacancies(self, table_num, master_key):
        vacant_rowids = []
        in_use_rowids = []
        f = Fernet(master_key)
        table = self.table_tuple[table_num]
        all_data = self.select_all(table)
        for row in all_data:
            in_use = cs.try_decrypt_wo_exceptions(row[2].encode(), f)
            if not in_use:
                vacant_rowids.append(row[0])
            elif in_use.decode() == 'in_use':
                in_use_rowids.append(row[0])
            else:
                raise Exception(f'Questionable: {in_use.decode()=}')
                print(in_use.decode())
                vacant_rowids.append(row[0])
        if len(vacant_rowids) < 3:
            self.add_dummy_data()
            start = max(*in_use_rowids, *vacant_rowids) + 1
            vacant_rowids = vacant_rowids + [i for i in range(start, start+10)]
        return [vacant_rowids, in_use_rowids]

    # insert key to table, change row status to in_use and add timestamp
    def insert_key(self, key, table_num, rowid, master_key):
        f = Fernet(master_key)
        timestamp = str(int(time.time()))
        data = (f.encrypt(key), f.encrypt('in_use'.encode()).decode(), f.encrypt(timestamp.encode()).decode())
        table = self.table_tuple[table_num]
        self.update_by_rowid(table, self.cols, data, rowid)
    
    # generate new key and add it to table
    def add_new_key(self, table_num, master_key):
        # table = self.table_tuple[table_num]
        available_rowids = self.find_vacancies(table_num, master_key)[0]
        # print(available_rowids)
        rowid = cs.secrets.choice(available_rowids)
        key = Fernet.generate_key()
        self.insert_key(key, table_num, rowid, master_key)
        return rowid, key

    # get the actual key
    def decrypt_key(self, encrypted_key, master_key):
        return Fernet(master_key).decrypt(encrypted_key)
    
    # return a dict with rowids as keys and (decrypted) keys as values
    def get_rows_and_keys(self, table_num, master_key):
        table = self.table_tuple[table_num]
        used_rowids = self.find_vacancies(table_num, master_key)[1]
        all_rows = self.select_all(table)
        rows_and_keys = dict()
        for row in all_rows:
            if row[0] in used_rowids:
                rows_and_keys[row[0]] = self.decrypt_key(row[1], master_key)
        return rows_and_keys


class DB_password(DB_general):

    def __init__(self, filepath_of_db) -> None:
        super().__init__(filepath_of_db)
        self.table_tuple = ('apps', 'emails', 'data')
    
    def add_dummy_data(self, data_type, num_of_rows=10):
        table = self.table_tuple[data_type]
        f = Fernet(Fernet.generate_key())
        t_tuple = type_tuples['password'][:len(self.tables[table].keys())]
        dummy_data = generate_dummy_data(t_tuple, num_of_rows, f)
        self.insert_many(table, self.tables[table].keys(), dummy_data)

    # get list of data_type (0 = apps or 1 = emails)
    def get_list(self, data_type, rows_and_keys):
        if data_type not in (0, 1):
            raise Exception(f'Invalid data type: {data_type=}')
        all_data = self.select_all(self.table_tuple[data_type])
        app_list = []
        for row in all_data:
            if row[0] in rows_and_keys:
                f = Fernet(rows_and_keys[row[0]])
                app_list.append(cs.decrypt_text(row[1], f))
        # for rowid, key in rows_and_keys.items():
        return app_list

    # find app (data_type = 0) of email (1) containing str_to_find
    def find(self, data_type, str_to_find, rows_and_keys):
        if data_type not in (0, 1):
            raise Exception(f'Invalid data type: {data_type=}')
        all_data = self.select_all(self.table_tuple[data_type])
        findings = []
        for row in all_data:
            if row[0] in rows_and_keys:
                f = Fernet(rows_and_keys[row[0]])
                name = cs.decrypt_text(row[1], f)
                if str_to_find.lower() in name.lower():
                    findings.append((row[0], name))
        return findings

    # find usernames and passwords related to app or email
    def find_password(self, data_type, rowid, rows_and_keys):
        if data_type not in (0, 1):
            raise Exception(f'Invalid data type: {data_type=}')
        all_data = self.select_all(self.table_tuple[-1])
        findings = []
        for row in all_data:
            if row[0] in rows_and_keys:
                f = Fernet(rows_and_keys[row[0]])
                things_to_add = False
                if not data_type and int(cs.decrypt_text(row[2], f)) == rowid:
                    things_to_add = True
                elif data_type and int(cs.decrypt_text(row[4], f)) == rowid:
                    things_to_add = True
                if things_to_add:
                    decrypted_row = cs.decrypt_text_list(row[1:], f)
                    findings.append(tuple([row[0]] + decrypted_row))
        return findings

    # data_type: 0 = app, 1 = email or 2 = data
    def insert_data(self, data_type, data, row_and_key):
        # choose table based on data_type
        try:
            table = self.table_tuple[data_type]
        except IndexError:
            raise Exception(f'Invalid data type: {data_type=}')
        # add timestamp, and encrypt
        data = list(data) + [str(int(time.time()))]
        f = Fernet(row_and_key[1])
        encrypted_data = cs.encrypt_text_list(data, f)
        columns = self.tables[table].keys()
        self.update_by_rowid(table, columns, encrypted_data, row_and_key[0])




