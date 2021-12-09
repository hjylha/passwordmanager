
import dbs
from dbs import PasswordNotFoundError, DB_auth, DB_keys, DB_password


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
        
    