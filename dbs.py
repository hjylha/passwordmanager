import time
from typing import Iterable, Optional

from cryptography.fernet import Fernet

from db_setup import table_data, type_tuples
from db_general import DB_general
import crypto_stuff as cs


# see if string is contained in some string in a list
def find_from_list(str_to_find: str, list_to_search: Iterable[tuple[int, str]], exact_match: bool =False) -> list[tuple[int, str]]:
    findings = []
    for rowid, name in list_to_search:
        if str_to_find.lower() in name.lower() and not exact_match:
            findings.append((rowid, name))
        elif str_to_find.lower() == name.lower():
            findings.append((rowid, name))
    return findings

# generate a dummy encrypted string, key or has
# def generate_dummy_string(type_of_string: str, fernet_obj: Optional[Fernet] =None, password_hasher: Optional[cs.argon2.PasswordHasher] =None) -> str | bytes:
def generate_dummy_string(type_of_string: str, fernet_obj: Optional[Fernet] =None, password_hasher: Optional[cs.argon2.PasswordHasher] =None):
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
# def generate_dummy_data(type_tuple: tuple[str], num_of_rows: int, fernet_obj: Optional[Fernet] =None, password_hasher: Optional[cs.argon2.PasswordHasher]=None) -> list[tuple[str | bytes]]:
def generate_dummy_data(type_tuple: tuple[str], num_of_rows: int, fernet_obj: Optional[Fernet] =None, password_hasher: Optional[cs.argon2.PasswordHasher]=None) -> list[tuple]:
    dummy_data = []
    for _ in range(num_of_rows):
        datarow = tuple(generate_dummy_string(t, fernet_obj, password_hasher) for t in type_tuple)
        dummy_data.append(datarow)
    return dummy_data


# initiate 'auth', 'keys' or 'password' db
def initiate_db(filepath, db_type: str, num_of_dummy_inserts: int =10) -> DB_general:
    # make sure we can access filepath
    if not filepath.parent.exists():
        filepath.parent.mkdir(parents=True, exist_ok=True)
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

    def __init__(self, filepath_of_db, num_of_dummy_inserts: int = 10) -> None:
        super().__init__(filepath_of_db)
        self.table = 'auth'
        self.cols = ('hash', 'master_key', 'date_modified')
        self.length = len(self.select_all(self.table))
        # check that it contains the required stuff
        # TODO: maybe improve these
        selection = self.select_all(self.table)
        if not selection:
            initiate_db(self.filepath, 'auth', num_of_dummy_inserts)
        if num := (num_of_dummy_inserts - len(selection)) > 0:
            initiate_db(self.filepath, 'auth', num)
        if len(self.select_all(self.table)[0]) != 4:
            raise Exception(f'Something is wrong with columns in table: {self.table}')

    def check_uniqueness_of_keys(self) -> bool:
        keys = tuple(row[0] for row in self.select_columns(self.table, self.cols[1:]))
        if len(keys) == len(set(keys)):
            return True
        # if len(keys) != len(set(keys)):
        return False

    def is_key_in_keys(self, key: bytes) -> bool:
        keys = tuple(row[0] for row in self.select_columns(self.table, self.cols[1:]))
        if key in keys:
            return True
        return False

    # check the given password and return the corresponding (encrypted) master key (and possibly rowid)
    def check_password(self, password: str, with_rowid: bool =False) -> bytes:
        content = self.select_columns(self.table, ('rowid', *self.cols[:2]))
        ph = cs.PasswordHasher()
        search_results = []
        for row in content:
            try:
                ph.verify(row[1], password)
                if with_rowid:
                    search_results.append((row[0], row[2]))
                else:
                    search_results.append(row[2])
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
    # return master key
    def add_password(self, password: str, salt: bytes, master_key: bytes =None, rowid: int =None) -> bytes:
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
        return master_key
    
    # get the actual master key
    def decrypt_key(self, encrypted_key: bytes, password: str, salt: bytes) -> bytes:
        f = cs.do_crypto_stuff(password, salt, 200_000)
        return f.decrypt(encrypted_key)


class DB_keys(DB_general):

    def __init__(self, filepath_of_db, num_of_dummy_inserts: int = 10) -> None:
        super().__init__(filepath_of_db)
        self.table_tuple = ('app_keys', 'email_keys', 'data_keys')
        self.cols = ('key', 'in_use', 'date_modified')
        # check that db has tables and some rows in those tables
        for table in self.table_tuple:
            selection = self.select_all(table)
            if not selection:
                initiate_db(self.filepath, 'keys', num_of_dummy_inserts)
                # raise Exception(f'No table in database: {table}')
            if num := (num_of_dummy_inserts - len(selection)) > 0:
                initiate_db(self.filepath, 'keys', num)
            if self.cols != tuple(self.tables[table].keys()):
                raise Exception(f'Something is wrong with columns in table: {table}')
            if not self.select_all(table):
                raise Exception(f'No rows in table: {table}')
    
    # add more dummy data
    def add_dummy_data(self, table_num: int, num_of_rows: int =10) -> None:
        t_tuple = type_tuples['keys']
        f = Fernet(Fernet.generate_key())
        dummy_data = generate_dummy_data(t_tuple, num_of_rows, f)
        table = self.table_tuple[table_num]
        self.insert_many(table, self.tables[table].keys(), dummy_data)

    # find rows that are not in use (and also rows that are)
    def find_vacancies(self, table_num: int, master_key: bytes) -> list[list[int], list[int]]:
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
            self.add_dummy_data(table_num)
            start = max(*in_use_rowids, *vacant_rowids) + 1
            vacant_rowids = vacant_rowids + [i for i in range(start, start+10)]
        return [vacant_rowids, in_use_rowids]

    # insert key to table, change row status to in_use and add timestamp
    def insert_key(self, key: bytes, table_num: int, rowid: int, master_key: bytes):
        f = Fernet(master_key)
        timestamp = str(int(time.time()))
        data = (f.encrypt(key), f.encrypt('in_use'.encode()).decode(), f.encrypt(timestamp.encode()).decode())
        table = self.table_tuple[table_num]
        self.update_by_rowid(table, self.cols, data, rowid)
    
    # generate new key and add it to table, returns row and key
    def add_new_key(self, table_num: int, master_key: bytes) -> tuple[int, bytes]:
        # table = self.table_tuple[table_num]
        available_rowids = self.find_vacancies(table_num, master_key)[0]
        # print(available_rowids)
        rowid = cs.secrets.choice(available_rowids)
        key = Fernet.generate_key()
        self.insert_key(key, table_num, rowid, master_key)
        return rowid, key

    # overwrite key based on rowid
    def remove_key(self, table_num: int, rowid: int) -> None:
        overwrite = generate_dummy_data(type_tuples['keys'], 1)[0]
        table = self.table_tuple[table_num]
        self.update_by_rowid(table, self.cols, overwrite, rowid)

    # get the actual key
    def decrypt_key(self, encrypted_key: bytes, master_key: bytes) -> bytes:
        return Fernet(master_key).decrypt(encrypted_key)
    
    # return a dict with rowids as keys and (decrypted) keys as values
    def get_rows_and_keys(self, table_num: int, master_key: bytes) -> dict[int, bytes]:
        table = self.table_tuple[table_num]
        used_rowids = self.find_vacancies(table_num, master_key)[1]
        all_rows = self.select_all(table)
        rows_and_keys = dict()
        for row in all_rows:
            if row[0] in used_rowids:
                rows_and_keys[row[0]] = self.decrypt_key(row[1], master_key)
        return rows_and_keys


class DB_password(DB_general):

    def __init__(self, filepath_of_db, num_of_dummy_inserts: int = 10) -> None:
        super().__init__(filepath_of_db)
        self.table_tuple = ('apps', 'emails', 'data')
        for table in self.table_tuple:
            selection = self.select_all(table)
            if not selection:
                initiate_db(self.filepath, 'password', num_of_dummy_inserts)
                # raise Exception(f'No table in database: {table}')
            if num := (num_of_dummy_inserts - len(selection)) > 0:
                initiate_db(self.filepath, 'password', num)
            if table_data['password'][table].keys() != self.tables[table].keys():
                raise Exception(f'Something is wrong with columns in table: {table}')
            if not self.select_all(table):
                raise Exception(f'No rows in table: {table}')
    
    def add_dummy_data(self, data_type: int, num_of_rows: int =10):
        table = self.table_tuple[data_type]
        f = Fernet(Fernet.generate_key())
        t_tuple = type_tuples['password'][:len(self.tables[table].keys())]
        dummy_data = generate_dummy_data(t_tuple, num_of_rows, f)
        self.insert_many(table, self.tables[table].keys(), dummy_data)

    # get list of data_type (0 = apps or 1 = emails)
    # def get_list(self, data_type: int, rows_and_keys: dict[int, bytes], w_rowid: bool = True) -> list[str] | list[tuple[int, str]]:
    def get_list(self, data_type: int, rows_and_keys: dict[int, bytes], w_rowid: bool = True) -> list:
        if data_type not in (0, 1):
            raise Exception(f'Invalid data type: {data_type=}')
        all_data = self.select_all(self.table_tuple[data_type])
        app_list = []
        for row in all_data:
            if row[0] in rows_and_keys:
                f = Fernet(rows_and_keys[row[0]])
                if w_rowid:
                    app_list.append((row[0], cs.decrypt_text(row[1], f)))
                else:
                    app_list.append(cs.decrypt_text(row[1], f))
        # for rowid, key in rows_and_keys.items():
        return app_list

    # find app (data_type = 0) of email (1) containing str_to_find
    def find(self, data_type: int, str_to_find: str, rows_and_keys: dict[int, bytes]) -> list[tuple[int, str]]:
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
    def find_password(self, data_type: int, rowid: int, rows_and_keys: dict[int, bytes]) -> list[tuple[int, str, int, str, int, str]]:
        if data_type not in (0, 1):
            raise Exception(f'Invalid data type: {data_type=}')
        all_data = self.select_all(self.table_tuple[-1])
        findings = []
        for row in all_data:
            if row[0] in rows_and_keys:
                f = Fernet(rows_and_keys[row[0]])
                decrypted_row = cs.decrypt_text_list(row[1:], f)
                things_to_add = False
                if data_type and int(decrypted_row[1]) == rowid:
                    things_to_add = True
                elif not data_type and int(decrypted_row[3]) == rowid:
                    things_to_add = True
                if things_to_add:
                    finding = (row[0], decrypted_row[0], int(decrypted_row[1]), decrypted_row[2], int(decrypted_row[3]), decrypted_row[4])
                    findings.append(finding)
        return findings

    # data_type: 0 = app, 1 = email or 2 = data
    def insert_data(self, data_type: int, data: Iterable[str], row_and_key: dict[int, bytes]) -> None:
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
    
    # insert new password or update password data
    # data of the form {'username': str, 'email': int, 'password': str, 'app_name': int, 'url': str}
    # def insert_password_data(self, data: dict[str, str | int], row_and_key: dict[int, bytes]) -> None:
    def insert_password_data(self, data: dict, row_and_key: dict[int, bytes]) -> None:
        # add some zeros to mess with numbers for no reason
        if 'app_name' in data:
            data['app_name'] = ''.join(['0' for _ in range(cs.secrets.randbelow(23))] + [str(data['app_name'])])
        if 'email' in data:
            data['email'] = ''.join(['0' for _ in range(cs.secrets.randbelow(23))] + [str(data['email'])])
        data['date_modified'] = str(int(time.time()))
        f = Fernet(row_and_key[1])
        encrypted_data = cs.encrypt_text_list(data.values(), f)
        columns = data.keys()
        self.update_by_rowid(self.table_tuple[2], columns, encrypted_data, row_and_key[0])

    # write nonsense over a row of data
    def delete_data(self, data_type: int, rowid: int) -> None:
        # choose table based on data_type
        try:
            table = self.table_tuple[data_type]
        except IndexError:
            raise Exception(f'Invalid data type: {data_type=}')
        columns = self.tables[table].keys()
        dummy_row = generate_dummy_data(type_tuples['password'][:len(columns)], 1)[0]
        self.update_by_rowid(table, columns, dummy_row, rowid)

    def change_password(self, new_password: str, row_and_key: tuple[int, bytes]) -> None:
        f = Fernet(row_and_key[1])
        encrypted_pw = cs.encrypt_text(new_password, f)
        self.update_by_rowid('data', ('password',), (encrypted_pw,), row_and_key[0])


