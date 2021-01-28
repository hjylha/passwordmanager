
import getpass
from crypto_stuff import load_salt, do_crypto_stuff, encrypt_text, decrypt_text, encrypt_text_list, decrypt_text_list
from db import add_to_info_table, get_master_table, get_info, get_app_list


def initiate_db():
    from db import reset_db, add_to_master_table
    from crypto_stuff import generate_salt, load_salt
    username = getpass.getuser()
    print("Initiating password database for user" + username + "...\n")
    reset_db()
    password_accepted = False
    while not(password_accepted):
        master_password = getpass.getpass(prompt='Please enter master password for password manager: ')
        master_password2 = getpass.getpass(prompt='Please enter the master password again: ')
        if master_password == master_password2:
            print("Master password created.\n")
            password_accepted = True
        else:
            print("Passwords you typed are not the same. Please try again.")
        # print("Generating salt file...")
        generate_salt()
        # print("Salt file generated. Please do not remove or modify it.")
        f = do_crypto_stuff(master_password, load_salt(), 100000)
        pw_encrypted = encrypt_text(master_password, master_password, f)
        un_encrypted = encrypt_text(username, master_password, f)
        add_to_master_table(un_encrypted, pw_encrypted)
        print("Password database initiated. Following files created:")
        print("pw.db")
        print("salt.txt")
        print("Please do not remove or modify these files outside of this password manager.")
        print("\n\n")
        return (master_password, f)


# starting text
print("Welcome to my Password Manager\n")

# check if DB has been initiated
master = get_master_table()
if master == None:
    print("Password database has not been initiated yet.")
    print("Do you want to initiate it? (Y/N)")
    answered = False
    while not(answered):
        answer = input()
        if answer.lower() == "y":
            answered = True
            print("\n")
            initiation_data = initiate_db()
        elif answer.lower() == "n":
            answered = True
            exit()

try:
    master_password = initiation_data[0]
    f = initiation_data[1]
except NameError:
    username = getpass.getuser()
    master_password = getpass.getpass(prompt='Enter the master password: ')
    f = do_crypto_stuff(master_password, load_salt(), 100000)
    # check that they are in the database
    master_d = decrypt_text_list(master, master_password, f)
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
        # TODO
        print("adding pw")
    elif action == "2":
        # TODO
        print("changing pw")
    elif action == "3":
        # TODO
        print("retrieving pw")
    elif action == "4":
        # TODO
        print("showing a list")
    else:
        print("Invalid input. Please choose 1, 2, 3, 4 or 0")
