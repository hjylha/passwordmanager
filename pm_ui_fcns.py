import os
import time
import getpass
if os.name == 'nt':
    import msvcrt
else:
    import sys
    import select

import pyperclip

from pm_class import is_valid_email
from crypto_stuff import generate_password



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
    pyperclip.copy('')

# ask to press enter to clear clipboard, this will be done automatically in timeout seconds
def end_prompt(timeout: int = 20):
    start_time = time.time()
    print('')
    print('Press ENTER to return back to menu. (This also clears clipboard)')
    if os.name == 'nt':
        while time.time() - start_time < timeout:
            print(f'\rThis is done automatically in {timeout- int(time.time() - start_time)} seconds ', end='', flush=True)
            if msvcrt.kbhit():
                if ord(msvcrt.getch()) == 13:
                    break
            time.sleep(0.1)
    else:
        # getpass.getpass()
        print(f'\rThis is done automatically in {timeout- int(time.time() - start_time)} seconds ', end=' ', flush=True)
        select.select([sys.stdin], [], [], timeout)
        # while time.time() - start_time < timeout:
        #     time_left = timeout - time.time() + start_time
        #     print(f'\rThis is done automatically in {int(time_left)} seconds ', end='', flush=True)
        #     ready, _, _ = select.select([sys.stdin], [], [], time_left)
        #     if ready:
        #         break
        #     time.sleep(0.1)
    clear_clipboard()
    print('')


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
def ask_for_password() -> str:
    # username = getpass.getpass('Enter your username: ')
    password = getpass.getpass('Enter the master password: ')
    return password
    # return (username, password)


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
                if pw:
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
