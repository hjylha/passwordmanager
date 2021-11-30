import string
import base64
import hashlib
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import argon2
from argon2 import PasswordHasher

# create the encryptor/decryptor thingie through password and salt
def do_crypto_stuff(password, given_salt, num_of_iterations):
    encoded_password = password.encode('utf-8')
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=given_salt, iterations=num_of_iterations)
    key = base64.urlsafe_b64encode(kdf.derive(encoded_password))
    return Fernet(key)

# then we can encrypt and decrypt:
def encrypt_text(text, fernet_thing):
    encoded_text = text.encode('utf-8')
    return fernet_thing.encrypt(encoded_text).decode('utf-8')

def decrypt_text(text, fernet_thing):
    encoded_text = text.encode('utf-8')
    return fernet_thing.decrypt(encoded_text).decode('utf-8')

def encrypt_text_list(text_list, fernet_thing):
    return [encrypt_text(text, fernet_thing) for text in text_list]

def decrypt_text_list(text_list, fernet_thing):
    return [decrypt_text(text, fernet_thing) for text in text_list]

# hashing passwords (and usernames?)
# the old way
def hash_text(text, salt, num_of_iterations=200_000):
    encoded_text = text.encode('utf-8')
    iteration = num_of_iterations + len(text) * 1000
    return hashlib.pbkdf2_hmac('sha256', encoded_text, salt, iteration)
    
def create_hash_storage(text, salt, num_of_iterations=200_000):
    key = hash_text(text, salt, num_of_iterations)
    stored_value = salt + key
    return stored_value

# the new way (with argon2)
def hash_password(password):
    ph = PasswordHasher()
    return ph.hash(password)

# check if hashed password = hash
def check_password_hash(hash, password):
    ph = PasswordHasher()
    try:
        if ph.verify(hash, password):
            return True
    except argon2.exceptions.VerifyMismatchError:
        return False

# hash a couple of values
def hash_tuple(a_tuple):
    ph = PasswordHasher()
    return tuple(ph.hash(item) for item in a_tuple)

def check_tuple(h_tuple, a_tuple):
    ph = PasswordHasher()
    for hash, text in zip(h_tuple, a_tuple):
        try:
            ph.verify(hash, text)
        except argon2.exceptions.VerifyMismatchError:
            return False
    return True


# get string of characters for password generator (0: all, 1: only letters and numbers)
def get_characters(mode=0):
    characters = string.ascii_letters + string.digits
    if not mode:
        extra_characters = '(,._-*~"<>/|!@#$%^&)+='
        return characters + extra_characters
    return characters

# generate password of given length with or without extra characters
def generate_password(length=20, choice=0):
    characters = get_characters(choice)
    return "".join(secrets.choice(characters) for _ in range(length))
