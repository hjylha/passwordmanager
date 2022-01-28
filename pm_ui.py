# import os
# import getpass
from typing import Optional

# import pyperclip

# from pm_class import is_valid_email
from pm_connect import connect_to_pm_dbs
from pm_ui_fcns import yes_or_no_question, get_master_password, get_info_from_user, get_changed_info, print_info
from pm_ui_fcns import how_to_generate_pw, generate_pw, reveal_password, obtain_password


# functions dealing with dbs are contained in a class
class PM_UI():

    def __init__(self, existing_and_not_default: bool =False, waiting_time: int =20) -> None:
        self.timeout = waiting_time
        self.pm = connect_to_pm_dbs(False, False)
        
        if not self.pm:
            print('Normal files not found.')
            if not existing_and_not_default:
                self.pm = connect_to_pm_dbs(True, False)
                if self.pm:
                    a = yes_or_no_question('Do you want to use default files?')
                    if a.lower() == 'n':
                        self.pm = None
                if not self.pm:
                    ans = yes_or_no_question('Do you want to initialize the Password Manager?')
                    if ans.lower() == 'y':
                            print('Initializing Password Manager databases...')
                            self.pm = connect_to_pm_dbs(True, True)
                            print('Password database initialized.')
                            master_password = get_master_password()
                            self.pm.add_master_password(master_password)
                            self.pm.set_name_lists()
    
    # re-init PM, only use this if it works
    def reconnect(self) -> None:
        self.pm = connect_to_pm_dbs(False, False)
        # files, _ = get_files(file_locations.paths)
        # self.pm = PM(files[0], DB_auth(files[1]), DB_keys(files[2]), DB_password(files[3]))
    
    
    def list_apps(self) -> None:
        print('These are the apps you have saved passwords for:')
        app_list = tuple(app for _, app in self.pm.app_list)
        for app in app_list:
            print('\t', app)
        print('')


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
            print('Adding password canceled.\n')
            return
        # while loop, since user might want to generate password again
        while True:
            # generate password
            gen_type = how_to_generate_pw()
            pw = generate_pw(gen_type)
            # if no password, cancel the process
            if not pw:
                print('Adding password canceled.\n')
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
            # db_line_new = (db_line[0], db_line[1], db_line[2], pw, db_line[4], db_line[5])
            db_line_new = (*db_line[:3], pw, *db_line[4:])
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
                    print('Updating cancelled.\n')
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
            print('Delete process cancelled.\n')
