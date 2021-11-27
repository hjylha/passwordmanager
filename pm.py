
# import os
import getpass
# import pyperclip
from crypto_stuff import do_crypto_stuff, encrypt_text, decrypt_text, encrypt_text_list, decrypt_text_list, create_hash_storage
from db import check_db, get_master_table
import crypto_db
from pm_setup import load_salt, initiate_db
from pm_data import default_db_filename, default_salt_filename
import pm_fcns as pm
import pg

db_filename = default_db_filename
salt_filename = default_salt_filename

# ask to press enter, and clear clipboard
def end_prompt():
    print("\n")
    getpass.getpass("Press ENTER to return back to menu. (This also clears clipboard)")
    pm.clear_clipboard()
    print("\n")


def password_manager(db_filename=default_db_filename, salt_filename=default_salt_filename):
    # starting text
    print("Welcome to my Password Manager\n")

    # check if DB has been initiated
    # is_initiated = check_db(db_filename)
    if check_db(db_filename):
        # if initiated, ask for username and password
        username = input("Enter your username: ")
        master_password = getpass.getpass(prompt='Enter the master password: ')
        f = do_crypto_stuff(master_password, load_salt(salt_filename), 100000)
        # check that they are in the database
        # master_d = crypto_db.get_master_table(master_password, f)
        master_h = get_master_table(db_filename)
        un_h = create_hash_storage(username, load_salt(salt_filename))
        pw_h = create_hash_storage(master_password, load_salt(salt_filename))
        # if not(username == master_d[0] and master_password == master_d[1]):
        if not(un_h == master_h[0] and pw_h == master_h[1]):
            print("Invalid password or username")
            exit()
    else:
        print("Password database has not been initiated yet.")
        # print("Do you want to initiate it? (Y/N)")
        answer = pm.yes_or_no_question("Do you want to initiate it?")
        if answer.lower() == "y":
            print("\n")
            initiation_data = initiate_db()
            username = initiation_data[0]
            master_password = initiation_data[1]
            f = initiation_data[2]
        else:
            exit()

    # maybe clear screen before starting
    pm.clear_screen()
    print("Password Manager for user", username, "\n")

    # the program loop
    while True:
        print("What do you want to do?")
        print("(1) Add a new password")
        print("(2) Change a password")
        print("(3) Retrieve a password")
        print("(4) Delete a password")
        print("(5) Show a list of apps with passwords")
        print("(0) Exit")
        action = input()
        if action == "0":
            exit()
        elif action == "1":
            pm.add_password(f)
            end_prompt()
        elif action == "2":
            pm.change_password(f)
            end_prompt()
        elif action == "3":
            pm.find_password_for_app(f)
            end_prompt()
        elif action == "4":
            pm.delete_password(f)
            end_prompt()
        elif action == "5":
            print("These are the apps you have saved passwords for:")
            app_list = crypto_db.get_app_list(f)
            for app in app_list:
                print("\t", app)
            print("\n")
            end_prompt()
        else:
            print("Invalid input. Please choose one of the options.\n")

if __name__ == '__main__':
    password_manager()
