import os
import getpass
from typing import Optional

import pyperclip

from dbs import initiate_db, DB_auth, DB_keys, DB_password
from pm_class import PM, is_valid_email
from crypto_stuff import generate_password
from file_handling import get_files
import file_locations


# some helpful fcns
def clear_screen():
    # for windows
    if os.name == 'nt':
        _ = os.system('cls')
    # for mac or linux
    else:
        _ = os.system('clear')

# overwrite clipboard
def clear_clipboard():
    pyperclip.copy('nothing here')


# ask user to set master password
def get_master_password() -> str:
    print('')
    while True:
        master_password = getpass.getpass(prompt='Please enter master password for password manager: ')
        master_password2 = getpass.getpass(prompt='Please enter the master password again: ')
        if master_password == master_password2:
            # is it ok if user just presses enter twice?
            print('Master password created.\n')
            return master_password
        print('Passwords you typed are not the same. Please try again.')

# ask for username and password
def ask_for_username_and_password() -> tuple[str, str]:
    username = getpass.getpass('Enter your username: ')
    password = getpass.getpass('Enter the master password: ')
    return (username, password)


# get the answer to a yes/no question from user, returns 'y' or 'n'
def yes_or_no_question(question_text: str) -> str:
    help_text = 'Please answer Y or N for yes or no.'
    while True:
        answer = input(f'{question_text} (Y/N) ')
        if answer.lower() == 'y':
            return 'y'
        if answer.lower() == 'n':
            return 'n'
        print(help_text)


# get app name, url of app, username and email associated with app from user
def get_info_from_user() -> tuple[str, str, str, str]:
    print('Write the name of the app you want to add password to:')
    app_name = input('\t')
    print('What is the internet address of this app?')
    url = input('\t')
    print('What is your username associated with this app?')
    username = input('\t')
    print('What is your email associated with this app?')
    email = input('\t')
    return (username, email, app_name, url)

def get_changed_info():
    new_info = dict()
    print('\n')
    # change app?
    ans = yes_or_no_question('Do you want to change the app name?')
    if ans == 'y':
        new_app_name = input('What is the new app name?   ')
        new_info['app_name'] = new_app_name
    # change username?
    ans = yes_or_no_question('Do you want to change the username?')
    if ans == 'y':
        new_username = input('What is the new username?   ')
        new_info['username'] = new_username
    # change email?
    ans = yes_or_no_question('Do you want to change the email?')
    if ans == 'y':
        new_email = input('What is the new email?   ')
        new_info['email'] = new_email
    # change app url?
    ans = yes_or_no_question('Do you want to change the url of the app?')
    if ans == 'y':
        new_url = input('What is the new url?   ')
        new_info['url'] = new_url
    print('\n')
    return new_info


# print a header line and a line (username, email, password, app, url)
def print_info(first_line: str, info: tuple[str, str, str, str, str]) -> None:
    print(first_line)
    print(f'Username: {info[0]}')
    print(f'Password: [HIDDEN]')
    email = info[1] if is_valid_email(info[1]) else '-'
    print(f'Email: {email}')
    # print(f'Email: {info[1]}')
    print(f'App name: {info[3]}')
    print(f'App url: {info[4]}')


# ask user how to generate password
def how_to_generate_pw() -> int:
    print('Do you want to')
    print('(1) Generate a password using letters, numbers and other characters')
    print('(2) Generate a password using only letters and numbers')
    print('(3) Come up with the password on my own')
    print('(0) Cancel')
    while True:
        sel = input()
        if sel in ('0', '1', '2', '3'):
            return int(sel)
        print('Please choose one of the options.')

# generate password (type_num = 1 or 2) or let the user come up with one (type_num = 3)
def generate_pw(type_num: int) -> str:
    # add the cancel password option just to be sure
    if type_num == 0:
        return ''
    # generate using all characters
    if type_num == 1:
        return generate_password()
    # generate using letters and numbers
    if type_num == 2:
        return generate_password(choice=1)
    # user makes the password (or saves an existing one to database)
    if type_num == 3:
        while True:
            pw = getpass.getpass('Type the password you want: ')
            pw2 = getpass.getpass('Type the password again: ')
            if pw == pw2:
                if pw != '':
                    return pw
                ans = yes_or_no_question('you did not type any password. Do you want to try again?')
                if ans == 'n':
                    return ''
            else:
                ans = yes_or_no_question('Passwords were not the same. Do you want to try again?')
                if ans == 'n':
                    return ''

# ask user how to reveal password
def reveal_password(pw: str) -> None:
        print('\nWhat do you want to do:')
        print('(1) Copy the password to clipboard')
        print('(2) Show the password')
        print('(0) Skip password reveal')
        while True:
            pick = input()
            if pick == '0':
                return
            if pick == '1':
                pyperclip.copy(pw)
                print('Password has been copied to the clipboard.')
                return
            if pick == '2':
                print(f'Password is: {pw}')
                return


# info = (rowid, username, email, password, app, url)
def obtain_password(info: tuple[int, str, str, str, str, str], reveal_pw: bool) -> None:
    print('\nPassword found.')
    print(f'App: {info[4]}')
    print(f'Username: {info[1]}')
    print(f'Email: {info[2]}')
    print(f'App url: {info[5]}')
    if reveal_pw:
        reveal_password(info[3])


# functions dealing with dbs are contained in a class
class PM_UI():

    def __init__(self) -> None:
        self.pm = None
        files, exists = get_files(file_locations.paths)
        if exists:
            self.pm = PM(files[0], DB_auth(files[1]), DB_keys(files[2]), DB_password(files[3]))
        print('Welcome to Password Manager')
    
    # re-init PM, only use this if it works
    def reconnect(self) -> None:
        files, _ = get_files(file_locations.paths)
        self.pm = PM(files[0], DB_auth(files[1]), DB_keys(files[2]), DB_password(files[3]))
    
    # initializing password manager
    def initiate_pm(self) -> None:
        # setup the databases
        files = get_files(file_locations.paths)[0]
        print('Initializing Password Manager databases...')
        initiate_db(files[1], 'auth')
        initiate_db(files[2], 'keys')
        initiate_db(files[3], 'password')
        self.pm = PM(files[0], DB_auth(files[1]), DB_keys(files[2]), DB_password(files[3]))
        print('Password database initialized.')
        # get master password from user
        master_password = get_master_password()
        self.pm.add_master_password(master_password)
        self.pm.set_name_lists()
    
    
    # back to established PM stuff
    # get the info and check that app and username are not already in database
    def get_unique_info_from_user(self) -> Optional[tuple[str, str, str, str]]:
        while True:
            # info = (username, email, app, url)
            info = get_info_from_user()
            if not(self.pm.find_password(info[2], True, info[0])):
                return info
            print(f'Password for user {info[0]} to app {info[2]} already in database.')
            ans = yes_or_no_question('Do you want to try again?')
            if ans == 'n':
                # return empty list if user does not want to try again
                return None

    # find correct app and username from users input
    def find_app_and_username(self, first_line: str) -> Optional[tuple[int, str, str, str, str, str]]:
        print(first_line)
        app_name = input('\t')
        results = self.pm.find_password(app_name)
        if not results:
            print(f'No passwords related to {app_name} found\n')
            return None
        if len(results) == 1:
            return results[0]
        # app_name might not be the actual name
        print(f'More than one password related to {app_name} in the database.')
        # selected = False
        while True:
            print('Select the correct app and username:')
            for i, result in enumerate(results):
                print(f'({str(i+1)}) App: {result[4]}')
                # blank_list = [' ' for _ in range(len(str(i+1)) + 2)]
                blank = ''.join([' ' for _ in str((i+1)*100)])
                print(blank, f'{blank} username: {result[1]}')
            print('(0) Cancel search')
            selection = input()
            try:
                index = int(selection) - 1
                if index == -1:
                    print('Search cancelled.')
                    return []
                try:
                    result = results[index]
                    return result
                except IndexError:
                    pass
            except ValueError:
                pass
    
    # find and reveal password based on users input
    def find_password_for_app(self) -> None:
        result = self.find_app_and_username('Write the name of the app you want password for:')
        if not result:
            return
        obtain_password(result, True)
    
    # try to add info into database. returns True if process is complete (added or cancelled)
    def save_password_to_db_or_not(self, info: tuple[str, str, str, str, str]) -> bool:
        answer = yes_or_no_question('Do you want to save this password to the database?')
        if answer == 'y':
            print_info('The following information will be saved to the database:', info)
            answer2 = yes_or_no_question('Do you want to proceed?')
            if answer2 == 'y':
                self.pm.force_add_password(*info)
                print(f'Password for user {info[0]} to app {info[3]} has been saved to the database.')
                return True
            if answer2 == 'n':
                answer3 = yes_or_no_question('Do you want to generate password again?')
                if answer3 == 'y':
                    return False
                if answer3 == 'n':
                    print('Adding password canceled.')
                    return True
        if answer == 'n':
            answer2 = yes_or_no_question('Do you want to generate password again?')
            if answer2 == 'y':
                return False
            if answer2 == 'n':
                print('Adding password canceled.')
                return True
    
    # db_line has (rowid, username, email, password, app, url)
    def change_password_in_db_or_not(self, db_line: tuple[int, str, str, str, str, str]) -> bool:
        answer = yes_or_no_question('Do you want to save this password to the database?')
        if answer == 'y':
            print_info('The following information will be updated in the database:', db_line[1:])
            answer2 = yes_or_no_question('Do you want to proceed?')
            if answer2 == 'y':
                self.pm.change_password(db_line[0], db_line[3])
                print('Password has been updated.')
                return True
            if answer2 == 'n':
                print('Changing password canceled.')
                return True
        if answer == 'n':
            answer2 = yes_or_no_question('Do you want to generate new password again?')
            if answer2 == 'y':
                return False
            if answer2 == 'n':
                print('Changing password canceled.')
                return True
    
    # the whole process of adding a new password into database
    def add_password(self) -> None:
        # get the info from user
        info = self.get_unique_info_from_user()
        # if user does not want to give info, back to the main menu
        if not info:
            print('Adding password canceled.')
            return
        # while loop, since user might want to generate password again
        while True:
            # generate password
            gen_type = how_to_generate_pw()
            pw = generate_pw(gen_type)
            # if no password, cancel the process
            if pw == '':
                print('Adding password canceled.')
                return
            # user might want to check the generated password
            if gen_type in (1, 2):
                print('Password has been generated.')
                reveal_password(pw)
            # finally, try to save the password
            db_line = (info[0], info[1], pw, info[2], info[3])
            if self.save_password_to_db_or_not(db_line):
                return
    
    # db_line has (rowid, username, email, password, app, url)
    def change_password_in_db(self, db_line: tuple[int, str, str, str, str, str]) -> None:
        while True:
            # generate password
            gen_type = how_to_generate_pw()
            pw = generate_pw(gen_type)
            # if no password, cancel the process
            if pw == '':
                print('Changing password canceled.')
                return
            # user might want to check the generated password
            if gen_type in (1, 2):
                print('Password has been generated.')
                reveal_password(pw)
            # try to update database
            db_line_new = (db_line[0], db_line[1], db_line[2], pw, db_line[4], db_line[5])
            if self.change_password_in_db_or_not(db_line_new):
                # if update succesful or user cancels, return to main menu
                return

    # the whole process of changing a password
    def change_password(self) -> None:
        result = self.find_app_and_username('What is the app you want to change password for?')
        # if nothing found, return to main menu
        if not result:
            return
        # show the app and username
        obtain_password(result, False)
        self.change_password_in_db(result)
    
    def change_password_info(self) -> None:
        result = self.find_app_and_username('What is the app whose information you want change?')
        if not result:
            return
        # show password info
        obtain_password(result, False)
        # ask user what should be changed
        # print('\n')
        while True:
            new_data = get_changed_info()
            new_line = list(result)
            for i, key in enumerate(('username', 'email', 'placeholder', 'app_name', 'url')):
                if key in new_data:
                    new_line[i+1] = new_data[key]
            print_info('The following information will be updated in the database:', new_line[1:])
            ans = yes_or_no_question('Do you want to proceed?')
            if ans == 'y':
                self.pm.update_password_data(result[0], new_data)
                print('Information has been updated.')
                return
            else:
                ans2 = yes_or_no_question('Do you want to try again?')
                if ans2 == 'n':
                    print('Updating cancelled.')
                    return
    
    def delete_password(self) -> None:
        result = self.find_app_and_username('What is the app whose password you want to delete')
        if not result:
            return
        print_info('The following information will be deleted from the database:', result[1:])
        ans = yes_or_no_question('Do you want to delete this information?')
        if ans == 'y':
            self.pm.delete_password(result[0])
            print('Password has been deleted from the database.')
        if ans == 'n':
            print('Delete process cancelled.')