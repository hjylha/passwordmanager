import os
import sys
from pathlib import Path
# from typing import Optional

import file_locations

file_name = __file__


# generate random string of bytes and store it in a file
def generate_salt(salt_path) -> bytes:
    with open(salt_path, 'wb') as f:
        salt = os.urandom(16)
        f.write(salt)
    return salt

# get the string of bytes from a file
def get_salt(salt_path) -> bytes:
    with open(salt_path, 'rb') as f:
        return f.read()

# get 
def get_drives() -> list[str]:
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return [f"{c}:" for c in letters if Path(f"{c}:").exists()]

# get a bunch of (Windows) folders where db files are searched from
def get_possible_starting_folders() -> tuple:
    environ_keys = ['APPDATA', 'LOCALAPPDATA', 'ONEDRIVE', 'PROGRAMFILES', 'PROGRAMFILES(X86)', 'PUBLIC', 'USERPROFILE']
    # environ_keys.append('HOMEPATH')
    folders = [os.environ[key] for key in environ_keys]
    folders += os.environ['PATH'].split(';')
    folders += get_drives()
    p_folders = [Path(folder) for folder in folders]
    p_folders.append(Path(file_name).parent.resolve())
    return tuple(p_folders)


# find an existing path from above folders
def find_path(path: str):
    # if not on Windows, use given paths directly
    if os.name != 'nt' and Path(path).exists():
        return Path(path)
    elif os.name != 'nt':
        return None
    possible_folders = get_possible_starting_folders()
    for folder in possible_folders:
        if Path(folder / path).exists():
            return folder / path
    else:
        return None

# find an existing path from a list of possibilities
def find_path_from_list(path_list):
    for path in path_list:
        if p := find_path(path):
            return p
    else:
        return None

def get_files(salt_and_akd_paths: tuple[tuple[str], tuple[str], tuple[str], tuple[str]]):
    # salt
    salt_path = find_path_from_list(salt_and_akd_paths[0])
    if not salt_path:
        salt_path = Path(salt_and_akd_paths[0][0])
        if not salt_path.parent.exists():
            salt_path.parent.mkdir(parents=True, exist_ok=True)
        generate_salt(salt_path)
    salt = get_salt(salt_path)
    # dbs
    exists = False
    auth_path = find_path_from_list(salt_and_akd_paths[1])
    keys_path = find_path_from_list(salt_and_akd_paths[2])
    data_path = find_path_from_list(salt_and_akd_paths[3])
    if auth_path and keys_path and data_path:
        exists = True
    else:
        # if a db is not found revert to default filepaths
        auth_path = Path(salt_and_akd_paths[1][0])
        keys_path = Path(salt_and_akd_paths[2][0])
        data_path = Path(salt_and_akd_paths[3][0])
    # exists = auth_path.exists() and keys_path.exists() and data_path.exists()
    return ((salt, auth_path, keys_path, data_path), exists)
    