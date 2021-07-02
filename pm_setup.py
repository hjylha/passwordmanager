import os
import getpass
from pm_data import default_db_filename, default_salt_filename
from db import reset_db
from crypto_stuff import do_crypto_stuff, create_hash_storage
import crypto_db

# default_db_filename = "pw.db"
# default_salt_filename = "salt.txt"

# only use this once
def generate_salt(filename=default_salt_filename):
    salt = os.urandom(16)
    with open(filename, "wb") as salt_file:
        salt_file.write(salt)
    return salt

def load_salt(filename=default_salt_filename):
    return open(filename, "rb").read()

def initiate_db(db_filename=default_db_filename, salt_filename=default_salt_filename):
    username = getpass.getuser()
    print("Initiating password database for user" + username + "...\n")
    reset_db(db_filename)
    password_accepted = False
    while not(password_accepted):
        master_password = getpass.getpass(prompt='Please enter master password for password manager: ')
        master_password2 = getpass.getpass(prompt='Please enter the master password again: ')
        if master_password == master_password2:
            print("Master password created.\n")
            password_accepted = True
        else:
            print("Passwords you typed are not the same. Please try again.")
    # print("Generating salt file...")
    local_salt = generate_salt(salt_filename)
    # print("Salt file generated. Please do not remove or modify it.")
    f = do_crypto_stuff(master_password, local_salt, 100000)
    # pw_encrypted = crypto_stuff.encrypt_text(master_password, master_password, f)
    # un_encrypted = crypto_stuff.encrypt_text(username, master_password, f)
    # db.add_to_master_table(un_encrypted, pw_encrypted, db_filename)
    crypto_db.add_master_table(username, master_password, f)
    print("Password database initiated. Following files created:")
    print(db_filename)
    print(salt_filename)
    print("Please do not remove or modify these files outside of this password manager.")
    input("Press ENTER to continue.")
    print("\n\n")
    return (master_password, f)
    