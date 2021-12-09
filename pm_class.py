
import dbs
from dbs import PasswordNotFoundError, DB_auth, DB_keys, DB_password
from tests.test_dbs import rows_and_keys


class PM():
    def __init__(self, db_auth, db_keys, db_data):
        self.dba = db_auth
        self.dbk = db_keys
        self.dbp = db_data
        # should this be here?
        self.master_key = None
    
    # get salt (from somewhere in the files...)
    def get_salt(self):
        # TODO: all of these salt things
        return b'\xc1\x95\xe15=\tm\xef\xecTH\x8e\xf5;/l'

    # generate salt (and put it in some file)
    def generate_salt(self):
        pass

    # add password (and generate master key) the first time
    def add_master_password(self, password):
        self.master_key = self.dba.add_password(password, self.get_salt())
        # self.master_key = self.dba.decrypt_key(encrypted_m_key, password, self.get_salt())
    
    # check that password is in db, and get master key
    def check_master_password(self, password):
        try:
            encrypted_m_key = self.dba.check_password(password)
            self.master_key = self.dba.decrypt_key(encrypted_m_key, password, self.get_salt())
            # return self.dba.decrypt_key(encrypted_m_key, password, salt)
            return True
        except PasswordNotFoundError:
            # print('Password not in database.')
            return False
        
    # change the password (and change master key, optionally)
    def change_master_password(self, old_password, new_password, change_master_key=True):
        rowid, e_master_key = self.dba.check_password(old_password, True)
        master_key = None
        if not change_master_key:
            # self.check_master_password(old_password)
            master_key = self.dba.decrypt_key(e_master_key, old_password, self.get_salt())
        self.master_key = self.dba.add_password(new_password, self.get_salt(), master_key, rowid)

    
    # into the real business
    # app_or_email = 0 for app, 1 for email
    def find_info(self, app_or_email, name):
        if not self.master_key:
            raise Exception('Master key not active')
        # get in-use rows and corresponding keys
        rows_and_keys = self.dbk.get_rows_and_keys(app_or_email, self.master_key)
        # search through the rows
        return self.dbp.find(app_or_email, name, rows_and_keys)

    # app_or_email = 0 for app, 1 for email
    def add_info(self, app_or_email, name):
        if not self.master_key:
            raise Exception('Master key not active')
        # check if name is already in db (not sure if this should be part of UI)
        list_of_similar_names = (name for _, name in self.find_info(app_or_email, name))
        if name in list_of_similar_names:
            return False
        # if name is not in db, add it
        row_and_key = self.dbk.add_new_key(app_or_email, self.master_key)
        
        # try:
        self.dbp.insert_data(app_or_email, (name, str(0)), row_and_key)
        # except Exception as exc:
        #     print('Exception', exc)
        #     print('This should be 2:', len(row_and_key))
        #     print('rowid:', row_and_key[0])
        #     print('key:', row_and_key[1])
        return True

    # check that no invalid tokens exist
    def check_keys(self):
        if not self.master_key:
            raise Exception('Master key not active')
        pass

    # get the possible rowids for app and email
    def prepare_to_add_password(self, app: str, email: str) -> list:
        findings = {app: self.find_info(0, app)}
        findings[email] = self.find_info(1, email)
        return findings

    # TODO: this should check if the data already exists
    def add_password(self, username: str, email_rowid: int, password: str, app_rowid: int, url: str) -> None:
        if not self.master_key:
            raise Exception('Master key not active')
        # add new key
        row_and_key = self.dbk.add_new_key(2, self.master_key)
        # add some zeros to mess with numbers for no reason
        email = ''.join(['0' for _ in range(dbs.cs.secrets.randbelow(23))] + [str(email_rowid)])
        app = ''.join(['0' for _ in range(dbs.cs.secrets.randbelow(23))] + [str(app_rowid)])
        data = (username, email, password, app, url)
        self.dbp.insert_data(2, data, row_and_key)

    def find_password(self, app: str) -> list:
        if not self.master_key:
            raise Exception('Master key not active')
        app_info = self.find_info(0, app)
        # print(f'{app_info=}')
        password_info = []
        for info in app_info:
            # print('app info has rowid:', info[0])
            pw_rows = self.dbp.find_password(0, info[0], self.dbk.get_rows_and_keys(2, self.master_key))
            # print(f'{pw_rows=}')
            password_info += pw_rows
        return password_info

    # changing and removing password depends on the rowid
    def change_password(self, rowid, new_password):
        if not self.master_key:
            raise Exception('Master key not active')
        row_and_key = (rowid, self.dbk.get_rows_and_keys(2, self.master_key)[rowid])
        self.dbp.change_password(new_password, row_and_key)

    def delete_password(self, rowid):
        if not self.master_key:
            raise Exception('Master key not active')
        # overwrite the row
        self.dbp.delete_data(2, rowid)
        # remove the corresponding key and change it to be vacant
        self.dbk.remove_key(2, rowid)
        
    