import os

# from simplecrypt import encrypt, decrypt
import cryptography
from base64 import b64encode, b64decode

def generate_salt():
    salt = os.urandom(16)
    with open("salt.txt", "wb") as salt_file:
        salt_file.write(salt)

def load_salt():
    return open("salt.txt", "rb").read()
