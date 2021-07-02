import os
import getpass
from pm_data import default_db_filename, default_salt_filename
from pm_fcns import yes_or_no_question
from db import reset_db, add_to_master_table
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


# get master username and password from the user
def get_master_username():
    while True:
        username = input("Please enter your username for password manager: ")
        question = "\nIs " + username + " the username you want?"
        ans = yes_or_no_question(question)
        if ans == "y":
            return username

def get_master_password():
    print("")
    while True:
        master_password = getpass.getpass(prompt='Please enter master password for password manager: ')
        master_password2 = getpass.getpass(prompt='Please enter the master password again: ')
        if master_password == master_password2:
            # is it ok if user just presses enter twice?
            print("Master password created.\n")
            return master_password
        print("Passwords you typed are not the same. Please try again.")


def initiate_db(db_filename=default_db_filename, salt_filename=default_salt_filename):
    # get username and password from user
    # username = getpass.getuser()
    username = get_master_username()
    print("Initiating password database for user " + username + "...\n")
    reset_db(db_filename)
    master_password = get_master_password()

    # create salt file
    local_salt = generate_salt(salt_filename)
    # print("Salt file generated. Please do not remove or modify it.")

    # hash username and password, and store them in database
    f = do_crypto_stuff(master_password, local_salt, 100000)
    un_hashed = create_hash_storage(username, local_salt)
    pw_hashed = create_hash_storage(master_password, local_salt)
    add_to_master_table(un_hashed, pw_hashed, db_filename)
    
    print("Password database initiated. Following files created:")
    print(db_filename)
    print(salt_filename)
    print("Please do not remove or modify these files outside of this password manager.")
    input("Press ENTER to continue.")
    print("\n\n")
    return (master_password, f)
    