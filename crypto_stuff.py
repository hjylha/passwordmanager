import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# only use this once
def generate_salt():
    salt = os.urandom(16)
    with open("salt.txt", "wb") as salt_file:
        salt_file.write(salt)

def load_salt():
    return open("salt.txt", "rb").read()

# encryption/decryption requires bytes instead of strings
# so we make the conversion
# also add salt
def prepare(text, password):
    # convert strings to bytes
    encoded_text = text.encode('utf-8')
    encoded_pw = password.encode('utf-8')
    # load the salt
    local_salt = load_salt()
    return (encoded_text, encoded_pw, local_salt)

def do_crypto_stuff(encoded_password, given_salt, num_of_iterations):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=given_salt, iterations=num_of_iterations)
    key = base64.urlsafe_b64encode(kdf.derive(encoded_password))
    return Fernet(key)

def encrypt_text(text, password):
    prep = prepare(text, password)
    # do crypto stuff
    f = do_crypto_stuff(prep[1], prep[2], 100000)
    # convert bytes to strings
    return f.encrypt(prep[0]).decode('utf-8')

def decrypt_text(text, password):
    prep = prepare(text, password)
    f = do_crypto_stuff(prep[1], prep[2], 100000)
    # convert bytes to strings
    return f.decrypt(prep[0]).decode('utf-8')

def encrypt_text_list(text_list, password):
    return [encrypt_text(text, password) for text in text_list]

def decrypt_text_list(text_list, password):
    return [decrypt_text(text, password) for text in text_list]