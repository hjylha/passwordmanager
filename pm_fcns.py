
import pyperclip
import os
import getpass
import crypto_db
import password_generator as pg


def clear_screen():
    # for windows
    if os.name == 'nt':
        _ = os.system('cls')
    # for mac or linux
    else:
        _ = os.system('clear')

# info = [username, email, password, app, url]
def obtain_password(info):
    print("Password found for", info[3], "user", info[0])
    reveal_password(info[2])
    # input("Press ENTER to continue")

def reveal_password(pw):
    print("What do you want to do:")
    print("(1) Copy the password to clipboard")
    print("(2) Show the password")
    completed = False
    while not(completed):
        pick = input()
        if pick == "1":
            pyperclip.copy(pw)
            print("Password has been copied to the clipboard.")
            completed = True
        elif pick == "2":
            print("Password is:", pw)
            completed = True

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

def save_password_to_db_or_not(info, master_pw, fernet_thing):
    answer = input("Do you want to save this password to the database? (Y/N) ")
    not_answered = True
    while not_answered:
        if answer.lower() == "y":
            not_answered = False
            crypto_db.add_info(info, master_pw, fernet_thing)
            print("The following information has been saved to the database:")
            print("username:", info[0])
            print("password:", "[HIDDEN]")
            print("email:", info[1])
            print("app name:", info[3])
            print("app url:", info[4])
            return True
        elif answer.lower == "n":
            ans = input("Do you want to generate password again? (Y/N)")
            while True:
                if ans.lower() == "y":
                    return False
                elif ans.lower() == "n":
                    print("Adding password canceled.")
                    return True
                else:
                    print("Please answer Y or N for yes of no.")
        else:
            print("Please answer Y or N for yes or no.")

# db_line has (rowid, username, email, password, app, url)
def change_password_in_db_or_not(db_line, master_pw, fernet_thing):
    answer = input("Do you want to save this password to the database? (Y/N) ")
    not_answered = True
    while not_answered:
        if answer.lower() == "y":
            not_answered = False
            # crypto_db.add_info(info, master_pw, fernet_thing)
            crypto_db.change_pw_in_row(db_line[0], db_line[3], master_pw, fernet_thing)
            print("The following information has been updated in the database:")
            print("username:", db_line[1])
            print("password:", "[HIDDEN]")
            print("email:", db_line[2])
            print("app name:", db_line[4])
            print("app url:", db_line[5])
            return True
        elif answer.lower == "n":
            ans = input("Do you want to generate new password again? (Y/N)")
            while True:
                if ans.lower() == "y":
                    return False
                elif ans.lower() == "n":
                    print("Changing password canceled.")
                    return True
                else:
                    print("Please answer Y or N for yes of no.")
        else:
            print("Please answer Y or N for yes or no.")
    

def find_password_for_app(master_pw, fernet_thing):
    print("Write the name of the app you want password for:")
    app_name = input("\t")
    results = crypto_db.get_info_for_app(app_name, master_pw, fernet_thing)
    if results == []:
        print("No passwords related to", app_name, "found\n")
        return
    elif len(results) == 1:
        obtain_password(results[0])
        return
    else:
        print("More than one password for", app_name, "in the database.")
        selected = False
        while not(selected):
            print("Select the correct username:")
            for i in range(len(results)):
                print("(" + str(i+1) + ")", results[i][0])
            selection = input()
            try:
                index = int(selection) - 1
                try:
                    result = results[index]
                    selected = True
                except IndexError:
                    pass
            except ValueError:
                pass
        obtain_password(result)
        return

def add_password(master_pw, fernet_thing):
    # info = (username, email, app, url)
    info = get_info_from_user()
    print("Do you want to")
    print("(1) Generate a password using letters, numbers and other characters")
    print("(2) Generate a password using only letters and numbers")
    print("(3) Come up with the password on my own")
    print("(0) Cancel")
    selected = False
    while not(selected):
        sel = input()
        pw_okd = False
        if sel == "1":
            selected = True
            while not(pw_okd):
                pw = pg.generate_password()
                print("Password has been generated.")
                reveal_password(pw)
                db_line = (info[0], info[1], pw, info[2], info[3])
                pw_okd = save_password_to_db_or_not(db_line, master_pw, fernet_thing)
        elif sel == "2":
            selected = True
            while not(pw_okd):
                pw = pg.generate_password(choice=1)
                print("Password has been generated.")
                reveal_password(pw)
                db_line = (info[0], info[1], pw, info[2], info[3])
                pw_okd = save_password_to_db_or_not(db_line, master_pw, fernet_thing)
        elif sel == "3":
            selected = True
            while not(pw_okd):
                pw = getpass.getpass("Type the password you want: ")
                pw2 = getpass.getpass("Type the password again: ")
                if pw == pw2:
                    db_line = (info[0], info[1], pw, info[2], info[3])
                    pw_okd = save_password_to_db_or_not(db_line, master_pw, fernet_thing)
                else:
                    ans = input("Passwords were not the same. Do you want to try again? (Y/N)")
                    while True:
                        if ans.lower() == "y":
                            pass
                        elif ans.lower() == "n":
                            print("Adding password canceled.")
                            return
        elif sel == "0":
            print("Adding password canceled.")
            selected = True
            return
        else:
            print("Please choose one of the options.")

# db_line has (rowid, username, email, password, app, url)
def change_password_in_db(db_line, master_pw, fernet_thing):
    print("Do you want to")
    print("(1) Generate a new password using letters, numbers and other characters")
    print("(2) Generate a new password using only letters and numbers")
    print("(3) Come up with the new password on my own")
    print("(0) Cancel")
    selected = False
    while not(selected):
        sel = input()
        pw_okd = False
        if sel == "1":
            selected = True
            while not(pw_okd):
                pw = pg.generate_password()
                print("Password has been generated.")
                reveal_password(pw)
                db_line_new = (db_line[0], db_line[1], db_line[2], pw, db_line[4], db_line[5])
                pw_okd = change_password_in_db_or_not(db_line_new, master_pw, fernet_thing)
                # pw_okd = save_password_to_db_or_not(db_line_new, master_pw, fernet_thing)
        elif sel == "2":
            selected = True
            while not(pw_okd):
                pw = pg.generate_password(choice=1)
                print("Password has been generated.")
                reveal_password(pw)
                db_line_new = (db_line[0], db_line[1], db_line[2], pw, db_line[4], db_line[5])
                pw_okd = change_password_in_db_or_not(db_line_new, master_pw, fernet_thing)
        elif sel == "3":
            selected = True
            while not(pw_okd):
                pw = getpass.getpass("Type the password you want: ")
                pw2 = getpass.getpass("Type the password again: ")
                if pw == pw2:
                    db_line_new = (db_line[0], db_line[1], db_line[2], pw, db_line[4], db_line[5])
                    pw_okd = change_password_in_db_or_not(db_line_new, master_pw, fernet_thing)
                    # pw_okd = save_password_to_db_or_not(db_line, master_pw, fernet_thing)
                else:
                    ans = input("Passwords were not the same. Do you want to try again? (Y/N)")
                    while True:
                        if ans.lower() == "y":
                            pass
                        elif ans.lower() == "n":
                            print("Adding password canceled.")
                            return
        elif sel == "0":
            print("Adding password canceled.")
            selected = True
            return
        else:
            print("Please choose one of the options.")

def change_password(master_pw, fernet_thing):
    print("What is the app you want to change password for?")
    app_name = input("\t")
    results = crypto_db.get_info_for_app_w_rowid(app_name, master_pw, fernet_thing)
    if results == []:
        print("No passwords related to", app_name, "found\n")
        return
    elif len(results) == 1:
        change_password_in_db(results[0], master_pw, fernet_thing)
    else:
        print("More than one password for", app_name, "in the database.")
        selected = False
        while not(selected):
            print("Select the correct username:")
            for i in range(len(results)):
                print("(" + str(i+1) + ")", results[i][0])
            selection = input()
            try:
                index = int(selection) - 1
                try:
                    result = results[index]
                    selected = True
                except IndexError:
                    pass
            except ValueError:
                pass
        change_password_in_db(result, master_pw, fernet_thing)
