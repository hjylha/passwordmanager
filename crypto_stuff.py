import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# encryption/decryption requires bytes instead of strings
# so we make the conversion
# also add salt
# def prepare(text, password):
#     # convert strings to bytes
#     encoded_text = text.encode('utf-8')
#     encoded_pw = password.encode('utf-8')
#     # load the salt
#     local_salt = load_salt()
#     return (encoded_text, encoded_pw, local_salt)

def do_crypto_stuff(password, given_salt, num_of_iterations):
    encoded_password = password.encode('utf-8')
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=given_salt, iterations=num_of_iterations)
    key = base64.urlsafe_b64encode(kdf.derive(encoded_password))
    return Fernet(key)

def encrypt_text(text, password, fernet_thing):
    encoded_text = text.encode('utf-8')
    return fernet_thing.encrypt(encoded_text).decode('utf-8')

def decrypt_text(text, password, fernet_thing):
    encoded_text = text.encode('utf-8')
    return fernet_thing.decrypt(encoded_text).decode('utf-8')

def encrypt_text_list(text_list, password, fernet_thing):
    return [encrypt_text(text, password, fernet_thing) for text in text_list]

def decrypt_text_list(text_list, password, fernet_thing):
    return [decrypt_text(text, password, fernet_thing) for text in text_list]