import string
import base64
import hashlib
import secrets
from typing import Iterator, Optional

import cryptography
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import argon2
from argon2 import PasswordHasher

# create the encryptor/decryptor thingie through password and salt
def do_crypto_stuff(password: str, given_salt: bytes, num_of_iterations: int) -> Fernet:
    encoded_password = password.encode('utf-8')
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=given_salt, iterations=num_of_iterations)
    key = base64.urlsafe_b64encode(kdf.derive(encoded_password))
    return Fernet(key)

# then we can encrypt and decrypt:
def encrypt_text(text: str, fernet_thing: Fernet) -> str:
    encoded_text = text.encode('utf-8')
    return fernet_thing.encrypt(encoded_text).decode('utf-8')

def decrypt_text(text: str, fernet_thing: Fernet) -> str:
    encoded_text = text.encode('utf-8')
    return fernet_thing.decrypt(encoded_text).decode('utf-8')

# wanted: no exceptions when trying to decrypt dummy data
def try_decrypt_wo_exceptions(encrypted_text: bytes, fernet_thing: Fernet) -> Optional[bytes]:
    try:
        return fernet_thing.decrypt(encrypted_text)
    except cryptography.fernet.InvalidToken:
        return None
    # except cryptography.exceptions.InvalidSignature:
        

def encrypt_text_list(text_list: Iterator[str], fernet_thing: Fernet) -> list[str]:
    return [encrypt_text(text, fernet_thing) for text in text_list]

def decrypt_text_list(text_list: Iterator[str], fernet_thing: Fernet) -> list[str]:
    return [decrypt_text(text, fernet_thing) for text in text_list]

# hashing passwords (and usernames?)
# the old way
def hash_text(text: str, salt: bytes, num_of_iterations: int =200_000) -> bytes:
    encoded_text = text.encode('utf-8')
    iteration = num_of_iterations + len(text) * 1000
    return hashlib.pbkdf2_hmac('sha256', encoded_text, salt, iteration)
    
def create_hash_storage(text: str, salt: bytes, num_of_iterations: int =200_000) -> bytes:
    key = hash_text(text, salt, num_of_iterations)
    stored_value = salt + key
    return stored_value

# the new way (with argon2)
def hash_password(password: str) -> str:
    ph = PasswordHasher()
    return ph.hash(password)

# check if hashed password = hash
def check_password_hash(hash: str, password: str) -> bool:
    ph = PasswordHasher()
    try:
        if ph.verify(hash, password):
            return True
    except argon2.exceptions.VerifyMismatchError:
        return False

# hash a couple of values (should not be needed)
def hash_tuple(a_tuple: Iterator[str]) -> tuple[str]:
    ph = PasswordHasher()
    return tuple(ph.hash(item) for item in a_tuple)

def check_tuple(h_tuple: Iterator[str], a_tuple: Iterator[str]) -> bool:
    ph = PasswordHasher()
    for hash, text in zip(h_tuple, a_tuple):
        try:
            ph.verify(hash, text)
        except argon2.exceptions.VerifyMismatchError:
            return False
    return True


# get string of characters for password generator (False: all, True: only letters and numbers)
def get_characters(choice: bool =False) -> str:
    characters = string.ascii_letters + string.digits
    if not choice:
        extra_characters = '(,._-*~"<>/|!@#$%^&)+='
        return characters + extra_characters
    return characters

# generate password of given length with or without extra characters
def generate_password(length: int =20, choice: bool =False) -> str:
    characters = get_characters(choice)
    return ''.join(secrets.choice(characters) for _ in range(length))
