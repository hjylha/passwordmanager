
# import os
import getpass
# import pyperclip
from crypto_stuff import do_crypto_stuff, encrypt_text, decrypt_text, encrypt_text_list, decrypt_text_list
# import db
from db import default_db_filename, check_db
import crypto_db
import pm_setup
from pm_setup import default_salt_filename
import pm_fcns as pm
import password_generator as pg

db_filename = default_db_filename
salt_filename = default_salt_filename

def end_prompt():
    input("Press ENTER to return back to menu.")
    print("\n")


def password_manager(db_filename=default_db_filename, salt_filename=default_salt_filename):
    # starting text
    print("Welcome to my Password Manager\n")

    # check if DB has been initiated
    # master = db.get_master_table(db_filename)
    is_initiated = check_db(db_filename)
    if not(is_initiated):
        print("Password database has not been initiated yet.")
        print("Do you want to initiate it? (Y/N)")
        answered = False
        while not(answered):
            answer = input()
            if answer.lower() == "y":
                answered = True
                print("\n")
                initiation_data = pm_setup.initiate_db()
            elif answer.lower() == "n":
                answered = True
                exit()

    try:
        master_password = initiation_data[0]
        f = initiation_data[1]
    except NameError:
        username = getpass.getuser()
        master_password = getpass.getpass(prompt='Enter the master password: ')
        f = do_crypto_stuff(master_password, pm_setup.load_salt(salt_filename), 100000)
        # check that they are in the database
        master_d = crypto_db.get_master_table(master_password, f)
        if not(username == master_d[0] and master_password == master_d[1]):
            print("Invalid password or username")
            exit()


    # username also used for encryption/decryption
    # maybe something better should be used?
    # username = getpass.getuser()
    # ask master password
    # master_password = getpass.getpass(prompt='Enter the master password: ')

    # some options how to make use of username and password
    # TODO
    # pw = master_password + username
    # h_user = username
    # h_pw = master_password

    # maybe clear screen before starting
    pm.clear_screen()
    print("Password Manager for user", username, "\n")

    # the program loop
    while True:
        print("What do you want to do?")
        print("(1) Add a new password")
        print("(2) Change a password")
        print("(3) Retrieve a password")
        print("(4) Show a list of apps with passwords")
        print("(0) Exit")
        action = input()
        if action == "0":
            exit()
        elif action == "1":
            pm.add_password(master_password, f)
            end_prompt()
        elif action == "2":
            pm.change_password(master_password, f)
            end_prompt()
        elif action == "3":
            pm.find_password_for_app(master_password, f)
            end_prompt()
        elif action == "4":
            print("These are the apps you have saved passwords for:")
            app_list = crypto_db.get_app_list(master_password, f)
            for app in app_list:
                print("\t", app)
            print("\n")
            end_prompt()
        else:
            print("Invalid input. Please choose one of the options.\n")

if __name__ == '__main__':
    password_manager()
