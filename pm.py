
# import os
import getpass
# import pyperclip
# from crypto_stuff import do_crypto_stuff, create_hash_storage
# from db import check_db, get_master_table
# import crypto_db
# from pm_setup import load_salt, initiate_db
# from pm_data import default_db_filename, default_salt_filename
# import pm_fcns as pm
from pm_ui import PM_UI
from pm_ui import clear_clipboard, clear_screen, yes_or_no_question, ask_for_password

# ask to press enter, and clear clipboard
def end_prompt():
    print('\n')
    getpass.getpass('Press ENTER to return back to menu. (This also clears clipboard)')
    clear_clipboard()
    print('\n')


def password_manager():
    # starting text
    # print('Welcome to my Password Manager\n')
    pm_ui = PM_UI()

    if pm_ui.pm is None:
        print('Not all the necessary files are present.')
        ans = yes_or_no_question('Do you want to initialize the Password Manager?')
        if ans.lower() == 'y':
            pm_ui.initiate_pm()
            clear_screen()
        else:
            exit()
    
    # un = 'placeholder username'
    if pm_ui.pm.master_key is None:
        # un, master_pw = ask_for_username_and_password()
        master_pw = ask_for_password()
        if pm_ui.pm.check_master_password(master_pw):
            pm_ui.pm.set_name_lists()
        else:
            print('Incorrect username and password')
            exit()

    # no need for master pw anymore
    master_pw = None
    clear_screen()
    # print(f'Password Manager for user {un}\n')

    # the program loop
    while True:
        print('What do you want to do?')
        print('(1) Add a new password')
        print('(2) Change a password')
        print('(3) Retrieve a password')
        print('(4) Change information related to a password')
        print('(5) Show a list of apps with passwords')
        print('(7) Delete a password')
        print('(9) Clear Screen')
        print('(0) Exit')
        action = input()
        if action == '0':
            ans = yes_or_no_question('Are you sure you want to exit Password Manager?')
            if ans.lower() == 'y':
                clear_screen()
                exit()
        elif action == '1':
            pm_ui.add_password()
            end_prompt()
        elif action == '2':
            pm_ui.change_password()
            end_prompt()
        elif action == '3':
            pm_ui.find_password_for_app()
            end_prompt()
        elif action == '4':
            pm_ui.change_password_info()
            end_prompt()
        elif action == '5':
            print('These are the apps you have saved passwords for:')
            app_list = [app for _, app in pm_ui.pm.app_list]
            for app in app_list:
                print('\t', app)
            print('\n')
            end_prompt()
        elif action == '7':
            pm_ui.delete_password()
            end_prompt()
        elif action == '9':
            clear_screen()
        else:
            print('Invalid input. Please choose one of the options.\n')

if __name__ == '__main__':
    password_manager()
