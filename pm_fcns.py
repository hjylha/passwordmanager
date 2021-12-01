
import pyperclip
import os
import getpass
import crypto_db
from crypto_stuff import generate_password
from db import delete_row


def clear_screen():
    # for windows
    if os.name == 'nt':
        _ = os.system('cls')
    # for mac or linux
    else:
        _ = os.system('clear')

# is it enough to just copy something to the clipboard, insted of clearing it?
def clear_clipboard():
    pyperclip.copy("nothing here")
    # in windows:
    # https://stackoverflow.com/questions/53226110/how-to-clear-clipboard-in-using-python/53226144
    # from ctypes import windll
    # if windll.user32.OpenClipboard(None):
    #     windll.user32.EmptyClipboard()
    #     windll.user32.CloseClipboard()
    # print("Clipboard cleared")


# print a header line and a line from database
def print_info(first_line, info):
    print(first_line)
    print("username:", info[0])
    print("password:", "[HIDDEN]")
    print("email:", info[1])
    print("app name:", info[3])
    print("app url:", info[4])

# get the answer to a yes/no question from user
def yes_or_no_question(question_text):
    help_text = "Please answer Y or N for yes or no."
    while True:
        answer = input(question_text + " (Y/N) ")
        if answer.lower() == "y":
            return "y"
        if answer.lower() == "n":
            return "n"
        print(help_text)

# info = [username, email, password, app, url]
def obtain_password(info, reveal_pw):
    # print("Password found for", info[4], "user", info[1])
    print("\nPassword found.")
    print("App:", info[4])
    print("Username:", info[1])
    if reveal_pw:
        reveal_password(info[3])
    # input("Press ENTER to continue")

def reveal_password(pw):
    print("\nWhat do you want to do:")
    print("(1) Copy the password to clipboard")
    print("(2) Show the password")
    print("(0) Skip password reveal")
    while True:
        pick = input()
        if pick == "0":
            return
        if pick == "1":
            pyperclip.copy(pw)
            print("Password has been copied to the clipboard.")
            return
        if pick == "2":
            print("Password is:", pw)
            return


# choose how to generate password
def how_to_generate_pw():
    print("Do you want to")
    print("(1) Generate a password using letters, numbers and other characters")
    print("(2) Generate a password using only letters and numbers")
    print("(3) Come up with the password on my own")
    print("(0) Cancel")
    while True:
        sel = input()
        if sel in ("0", "1", "2", "3"):
            return int(sel)
        print("Please choose one of the options.")

# generate password (type_num = 1 or 2) or let the user come up with one (type_num = 3)
def generate_pw(type_num):
    # add the cancel password option just to be sure
    if type_num == 0:
        return ""
    # generate using all characters
    if type_num == 1:
        return generate_password()
    # generate using letters and numbers
    if type_num == 2:
        return generate_password(choice=1)
    # user makes the password (or saves an existing one to database)
    if type_num == 3:
        while True:
            pw = getpass.getpass("Type the password you want: ")
            pw2 = getpass.getpass("Type the password again: ")
            if pw == pw2:
                if pw != "":
                    return pw
                ans = yes_or_no_question("you did not type any password. Do you want to try again?")
                if ans == "n":
                    return ""
            else:
                ans = yes_or_no_question("Passwords were not the same. Do you want to try again?")
                if ans == "n":
                    return ""


# get app name, url of app, username and email associated with app from user
def get_info_from_user():
    print("Write the name of the app you want to add password to:")
    app_name = input("\t")
    print("What is the internet address of this app?")
    url = input("\t")
    print("What is your username associated with this app?")
    un = input("\t")
    print("What is your email associated with this app?")
    email = input("\t")
    return (un, email, app_name, url)

# get the info and check that app and username are not already in database
def get_unique_info_from_user(fernet_thing):
    while True:
        # info = (username, email, app, url)
        info = get_info_from_user()
        if not(crypto_db.is_info_in_db(info, fernet_thing)):
            return info
        print("Password for user", info[0], "to app", info[2], "already in database.")
        ans = yes_or_no_question("Do you want to try again?")
        if ans == "n":
            # return empty list if user does not want to try again
            return []

# find correct app and username from users input
def find_app_and_username(first_line, fernet_thing):
    print(first_line)
    app_name = input("\t")
    results = crypto_db.get_info_for_app_w_rowid(app_name, fernet_thing)
    if results == []:
        print("No passwords related to", app_name, "found\n")
        return []
    if len(results) == 1:
        return results[0]
    # app_name might not be the actual name
    print("More than one password related to", app_name, "in the database.")
    # selected = False
    while True:
        print("Select the correct app and username:")
        for i in range(len(results)):
            print("(" + str(i+1) + ")", "App:", results[i][4])
            # blank_list = [" " for _ in range(len(str(i+1)) + 2)]
            blank = "".join([" " for _ in range(len(str(i+1)) + 2)])
            print(blank, "username:", results[i][1])
        print("(0) Cancel search")
        selection = input()
        try:
            index = int(selection) - 1
            if index == -1:
                print("Search cancelled.")
                return []
            try:
                result = results[index]
                return result
            except IndexError:
                pass
        except ValueError:
            pass

# find and reveal password based on users input
def find_password_for_app(fernet_thing):
    result = find_app_and_username("Write the name of the app you want password for:", fernet_thing)
    if result == []:
        return
    obtain_password(result, True)


# try to add info into database. returns True if process is complete (added or cancelled)
def save_password_to_db_or_not(info, fernet_thing):
    answer = yes_or_no_question("Do you want to save this password to the database?")
    if answer == "y":
        print_info("The following information will be saved to the database:", info)
        answer2 = yes_or_no_question("Do you want to proceed?")
        if answer2 == "y":
            crypto_db.add_info(info, fernet_thing)
            print("Password for user " + info[0] + " to app " + info[3] + " has been saved to the database.")
            return True
        if answer2 == "n":
            answer3 = yes_or_no_question("Do you want to generate password again?")
            if answer3 == "y":
                return False
            if answer3 == "n":
                print("Adding password canceled.")
                return True
    if answer == "n":
        answer2 = yes_or_no_question("Do you want to generate password again?")
        if answer2 == "y":
            return False
        if answer2 == "n":
            print("Adding password canceled.")
            return True

# db_line has (rowid, username, email, password, app, url)
def change_password_in_db_or_not(db_line, fernet_thing):
    answer = yes_or_no_question("Do you want to save this password to the database?")
    if answer == "y":
        print_info("The following information will be updated in the database:", db_line[1:])
        answer2 = yes_or_no_question("Do you want to proceed?")
        if answer2 == "y":
            crypto_db.change_pw_in_row(db_line[0], db_line[3], fernet_thing)
            print("Password has been updated.")
            return True
        if answer2 == "n":
            print("Changing password canceled.")
            return True
    if answer == "n":
        answer2 = yes_or_no_question("Do you want to generate new password again?")
        if answer2 == "y":
            return False
        if answer2 == "n":
            print("Changing password canceled.")
            return True


# the whole process of adding a new password into database
def add_password(fernet_thing):
    # get the info from user
    info = get_unique_info_from_user(fernet_thing)
    # if user does not want to give info, back to the main menu
    if info == []:
        print("Adding password canceled.")
        return
    # while loop, since user might want to generate password again
    while True:
        # generate password
        gen_type = how_to_generate_pw()
        pw = generate_pw(gen_type)
        # if no password, cancel the process
        if pw == "":
            print("Adding password canceled.")
            return
        # user might want to check the generated password
        if gen_type in (1, 2):
            print("Password has been generated.")
            reveal_password(pw)
        # finally, try to save the password
        db_line = (info[0], info[1], pw, info[2], info[3])
        if save_password_to_db_or_not(db_line, fernet_thing):
            return

# db_line has (rowid, username, email, password, app, url)
def change_password_in_db(db_line, fernet_thing):
    while True:
        # generate password
        gen_type = how_to_generate_pw()
        pw = generate_pw(gen_type)
        # if no password, cancel the process
        if pw == "":
            print("Changing password canceled.")
            return
        # user might want to check the generated password
        if gen_type in (1, 2):
            print("Password has been generated.")
            reveal_password(pw)
        # try to update database
        db_line_new = (db_line[0], db_line[1], db_line[2], pw, db_line[4], db_line[5])
        if change_password_in_db_or_not(db_line_new, fernet_thing):
            # if update succesful or user cancels, return to main menu
            return

# the whole process of changing a password
def change_password(fernet_thing):
    result = find_app_and_username("What is the app you want to change password for?", fernet_thing)
    # if nothing found, return to main menu
    if result == []:
        return
    # show the app and username
    obtain_password(result, False)
    change_password_in_db(result, fernet_thing)

def delete_password(fernet_thing):
    result = find_app_and_username("What is the app whose password you want to delete", fernet_thing)
    if result == []:
        return
    print_info("The following information will be deleted from the database:", result[1:])
    ans = yes_or_no_question("Do you want to delete this information?")
    if ans == "y":
        delete_row(result[0])
        print("Password has been deleted from the database.")
    if ans == "n":
        print("Delete process cancelled.")
