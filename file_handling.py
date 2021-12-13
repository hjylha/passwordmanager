import os
from pathlib import Path

import file_locations


def get_drives():
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return [f"{c}:" for c in letters if Path(f"{c}:").exists()]

def generate_salt(salt_path):
    with open(salt_path, 'wb') as f:
        f.write(os.urandom(16))

def get_salt(salt_path):
    with open(salt_path, 'rb') as f:
        return f.read()

def get_files():
    # salt
    salt_path = Path(file_locations.salt_path)
    if not salt_path.parent.exists():
        salt_path.parent.mkdir(parents=True, exist_ok=True)
    if not salt_path.exists():
        generate_salt(salt_path)
    salt = get_salt(salt_path)
    # dbs
    auth_path = Path(file_locations.db_auth_path)
    keys_path = Path(file_locations.db_keys_path)
    data_path = Path(file_locations.db_data_path)
    exists = auth_path.exists() and keys_path.exists() and data_path.exists()
    return ((salt, auth_path, keys_path, data_path), exists)
    