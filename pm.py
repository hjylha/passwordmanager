
import getpass

# username also used for encryption/decryption
username = getpass.getuser()
# ask master password
master_password = getpass.getpass(prompt='Enter the master password: ')

# hash username and master password
# TODO
h_user = username
h_pw = master_password

# check that they are in the database
# TODO

# if everything is ok, set key
# TODO
key = master_password + username


# use key to encrypt/decrypt database stuff


