import os
import getpass

import pyperclip

from dbs import initiate_db, DB_auth, DB_keys, DB_password
from pm_class import PM
from crypto_stuff import generate_password
from file_handling import get_files


# some helpful fcns
def clear_screen():
    # for windows
    if os.name == 'nt':
        _ = os.system('cls')
    # for mac or linux
    else:
        _ = os.system('clear')

def clear_clipboard():
    pyperclip.copy('nothing here')


class PM_UI():

    def __init__(self) -> None:
        self.pm = None
        # TODO: check if the db files exist
        files, exists = get_files()
        if exists:
            self.pm = PM(files[0], DB_auth(files[1]), DB_keys(files[2]), DB_password(files[3]))
        print('Welcome to Password Manager')
    
    # re-init PM, only use this if it works
    def reconnect(self):
        files, _ = get_files()
        self.pm = PM(files[0], DB_auth(files[1]), DB_keys(files[2]), DB_password(files[3]))
    
    # mothods for initializing password manager
    def get_master_password(self):
        print('')
        while True:
            master_password = getpass.getpass(prompt='Please enter master password for password manager: ')
            master_password2 = getpass.getpass(prompt='Please enter the master password again: ')
            if master_password == master_password2:
                # is it ok if user just presses enter twice?
                print('Master password created.\n')
                return master_password
            print('Passwords you typed are not the same. Please try again.')
        
    def initiate_pm(self):
        # setup the databases
        files = get_files()[0]
        print('Initializing Password Manager databases...')
        initiate_db(files[1], 'auth')
        initiate_db(files[2], 'keys')
        initiate_db(files[3], 'password')
        self.pm = PM(files[0], DB_auth(files[1]), DB_keys(files[2]), DB_password(files[3]))
        print('Password database initialized.')
        # get master password from user
        master_password = self.get_master_password()
        self.pm.add_master_password(master_password)
        self.pm.set_name_lists()
    
    

    # back to established PM stuff
    # ask for username and password
    def ask_for_username_and_password(self):
        username = getpass.getpass('Enter your username: ')
        password = getpass.getpass('Enter the master password: ')
        return (username, password)
    
    # print a header line and a line from database
    def print_info(self, first_line, info):
        print(first_line)
        print(f'username: {info[0]}')
        print(f'password: [HIDDEN]')
        print(f'email: {info[1]}')
        print(f'app name: {info[3]}')
        print(f'app url: {info[4]}')
    
    # get the answer to a yes/no question from user
    def yes_or_no_question(self, question_text):
        help_text = 'Please answer Y or N for yes or no.'
        while True:
            answer = input(f'{question_text} (Y/N) ')
            if answer.lower() == 'y':
                return 'y'
            if answer.lower() == 'n':
                return 'n'
            print(help_text)
    
    def reveal_password(self, pw):
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

    # info = [username, email, password, app, url]
    def obtain_password(self, info, reveal_pw):
        # print('Password found for', info[4], 'user', info[1])
        print('\nPassword found.')
        print('App:', info[4])
        print('Username:', info[1])
        if reveal_pw:
            self.reveal_password(info[3])
        # input('Press ENTER to continue')

    # choose how to generate password
    def how_to_generate_pw(self):
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
    def generate_pw(self, type_num):
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
                    ans = self.yes_or_no_question('you did not type any password. Do you want to try again?')
                    if ans == 'n':
                        return ''
                else:
                    ans = self.yes_or_no_question('Passwords were not the same. Do you want to try again?')
                    if ans == 'n':
                        return ''
    
    # get app name, url of app, username and email associated with app from user
    def get_info_from_user(self):
        print('Write the name of the app you want to add password to:')
        app_name = input('\t')
        print('What is the internet address of this app?')
        url = input('\t')
        print('What is your username associated with this app?')
        un = input('\t')
        print('What is your email associated with this app?')
        email = input('\t')
        return (un, email, app_name, url)
    
    # get the info and check that app and username are not already in database
    def get_unique_info_from_user(self):
        while True:
            # info = (username, email, app, url)
            info = self.get_info_from_user()
            if not(self.pm.find_password(info[2], True, info[0])):
                return info
            print(f'Password for user {info[0]} to app {info[2]} already in database.')
            ans = self.yes_or_no_question('Do you want to try again?')
            if ans == 'n':
                # return empty list if user does not want to try again
                return []

    # find correct app and username from users input
    def find_app_and_username(self, first_line):
        print(first_line)
        app_name = input('\t')
        results = self.pm.find_password(app_name)
        if results == []:
            print(f'No passwords related to {app_name} found\n')
            return []
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
    def find_password_for_app(self):
        result = self.find_app_and_username('Write the name of the app you want password for:')
        if result == []:
            return
        self.obtain_password(result, True)
    
    # try to add info into database. returns True if process is complete (added or cancelled)
    def save_password_to_db_or_not(self, info):
        answer = self.yes_or_no_question('Do you want to save this password to the database?')
        if answer == 'y':
            self.print_info('The following information will be saved to the database:', info)
            answer2 = self.yes_or_no_question('Do you want to proceed?')
            if answer2 == 'y':
                self.pm.force_add_password(*info)
                print(f'Password for user {info[0]} to app {info[3]} has been saved to the database.')
                return True
            if answer2 == 'n':
                answer3 = self.yes_or_no_question('Do you want to generate password again?')
                if answer3 == 'y':
                    return False
                if answer3 == 'n':
                    print('Adding password canceled.')
                    return True
        if answer == 'n':
            answer2 = self.yes_or_no_question('Do you want to generate password again?')
            if answer2 == 'y':
                return False
            if answer2 == 'n':
                print('Adding password canceled.')
                return True
    
    # db_line has (rowid, username, email, password, app, url)
    def change_password_in_db_or_not(self, db_line):
        answer = self.yes_or_no_question('Do you want to save this password to the database?')
        if answer == 'y':
            self.print_info('The following information will be updated in the database:', db_line[1:])
            answer2 = self.yes_or_no_question('Do you want to proceed?')
            if answer2 == 'y':
                # crypto_db.change_pw_in_row(db_line[0], db_line[3], fernet_thing)
                self.pm.change_password(db_line[0], db_line[3])
                print('Password has been updated.')
                return True
            if answer2 == 'n':
                print('Changing password canceled.')
                return True
        if answer == 'n':
            answer2 = self.yes_or_no_question('Do you want to generate new password again?')
            if answer2 == 'y':
                return False
            if answer2 == 'n':
                print('Changing password canceled.')
                return True
    
    # the whole process of adding a new password into database
    def add_password(self):
        # get the info from user
        info = self.get_unique_info_from_user()
        # if user does not want to give info, back to the main menu
        if info == []:
            print('Adding password canceled.')
            return
        # while loop, since user might want to generate password again
        while True:
            # generate password
            gen_type = self.how_to_generate_pw()
            pw = self.generate_pw(gen_type)
            # if no password, cancel the process
            if pw == '':
                print('Adding password canceled.')
                return
            # user might want to check the generated password
            if gen_type in (1, 2):
                print('Password has been generated.')
                self.reveal_password(pw)
            # finally, try to save the password
            db_line = (info[0], info[1], pw, info[2], info[3])
            if self.save_password_to_db_or_not(db_line):
                return
    
    # db_line has (rowid, username, email, password, app, url)
    def change_password_in_db(self, db_line):
        while True:
            # generate password
            gen_type = self.how_to_generate_pw()
            pw = self.generate_pw(gen_type)
            # if no password, cancel the process
            if pw == '':
                print('Changing password canceled.')
                return
            # user might want to check the generated password
            if gen_type in (1, 2):
                print('Password has been generated.')
                self.reveal_password(pw)
            # try to update database
            db_line_new = (db_line[0], db_line[1], db_line[2], pw, db_line[4], db_line[5])
            if self.change_password_in_db_or_not(db_line_new):
                # if update succesful or user cancels, return to main menu
                return

    # the whole process of changing a password
    def change_password(self):
        result = self.find_app_and_username('What is the app you want to change password for?')
        # if nothing found, return to main menu
        if result == []:
            return
        # show the app and username
        self.obtain_password(result, False)
        self.change_password_in_db(result)
    
    def delete_password(self):
        result = self.find_app_and_username('What is the app whose password you want to delete')
        if result == []:
            return
        self.print_info('The following information will be deleted from the database:', result[1:])
        ans = self.yes_or_no_question('Do you want to delete this information?')
        if ans == 'y':
            # delete_row(result[0])
            self.pm.delete_password(result[0])
            print('Password has been deleted from the database.')
        if ans == 'n':
            print('Delete process cancelled.')