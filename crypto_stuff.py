import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# create the encryptor/decryptor thingie through password and salt
def do_crypto_stuff(password, given_salt, num_of_iterations):
    encoded_password = password.encode('utf-8')
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=given_salt, iterations=num_of_iterations)
    key = base64.urlsafe_b64encode(kdf.derive(encoded_password))
    return Fernet(key)

# then we can encrypt and decrypt:
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

# hashing passwords (and usernames?)
def hash_text(text, salt, num_of_iterations=200_000):
    encoded_text = text.encode('utf-8')
    iteration = num_of_iterations + len(text) * 1000
    return hashlib.pbkdf2_hmac('sha256', encoded_text, salt, iteration)
    
def create_hash_storage(text, salt, num_of_iterations=200_000):
    key = hash_text(text, salt, num_of_iterations)
    stored_value = salt + key
    return stored_value