
import getpass
from crypto_stuff import encrypt_text, decrypt_text, encrypt_text_list, decrypt_text_list
from db import add_to_info_table, get_master_table, get_info, get_app_list


# starting text
print("Welcome to my Password Manager\n")

# check if DB has been initiated
master = get_master_table()
if master == None:
    # initiate DB
    # TODO
    print("Feature not added yet")
    exit()

# username also used for encryption/decryption
username = getpass.getuser()
# ask master password
master_password = getpass.getpass(prompt='Enter the master password: ')

# some options how to make use of username and password
# TODO
# pw = master_password + username
# h_user = username
# h_pw = master_password

# check that they are in the database
master_d = decrypt_text_list(master, master_password)
if not(username == master_d[0] and master_password == master_d[1]):
    print("Invalid password or username")
    exit()

print("Password Manager for user", username)

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
