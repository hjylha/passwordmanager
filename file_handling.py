import os
import sys
from pathlib import Path
# from typing import Optional

# not sure if there is a better way to make sure fcns use filepath of this file
file_handling_filename = __file__


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
    if os.name == 'nt':
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return [f"{c}:/" for c in letters if Path(f"{c}:").exists()]
    else:
        return ['/']

# get a bunch of (Windows) folders where db files are searched from
def get_possible_starting_folders() -> tuple:
    if os.name == 'nt':
        environ_keys = ['APPDATA', 'LOCALAPPDATA', 'ONEDRIVE', 'PROGRAMFILES', 'PROGRAMFILES(X86)', 'PUBLIC', 'USERPROFILE']
    else:
        environ_keys = ['HOME', 'PWD']
    # environ_keys.append('HOMEPATH')
    folders = [os.environ[key] for key in environ_keys]
    if os.name == 'nt':
        folders += os.environ['PATH'].split(';')
    folders += get_drives()
    p_folders = [Path(folder) for folder in folders]
    # add the folder this file is in to the list
    p_folders.append(Path(file_handling_filename).parent.resolve())
    # finally add the current work directory as well
    p_folders.append(Path.cwd().resolve())
    return tuple(p_folders)


# find an existing path from above folders
def find_path(path: str):
    # absolute path works
    if Path(path).exists():
        return Path(path).resolve()
    possible_folders = get_possible_starting_folders()
    for folder in possible_folders:
        if Path(folder / path).exists():
            return Path(folder / path).resolve()
    else:
        return None

# find an existing path from a list of possibilities. if default_is_ok is False, this ignores the first path
def find_path_from_list(path_list, default_is_ok=True):
    for i, path in enumerate(path_list):
        if p := find_path(path):
            if default_is_ok or i > 0:
                return (p, i)
    else:
        return None

# find multiple existing paths from a list of possibilities
def find_all_paths_from_list(path_list):
    paths = []
    for i, path in enumerate(path_list):
        if p:= find_path(path):
            paths.append((p, i))
    if paths:
        return tuple(paths)
    return None

def get_files(salt_and_akd_paths: tuple[tuple[str], tuple[str], tuple[str], tuple[str]], default_is_ok: bool =True) -> tuple[tuple, bool]:
    # remember which paths are found (if they are all 0, it means default)
    # indices = []
    # salt
    salt_exists = True
    salt_path = find_path_from_list(salt_and_akd_paths[0], default_is_ok)
    if not salt_path:
        salt_exists = False
        salt_path = (Path(file_handling_filename).parent / salt_and_akd_paths[0][0], 0)
        if not salt_path[0].exists():
            if not salt_path[0].parent.exists():
                salt_path[0].parent.mkdir(parents=True, exist_ok=True)
            generate_salt(salt_path[0])
    salt = get_salt(salt_path[0])
    # indices.append(salt_path[1])
    # dbs
    exists = False
    db_paths = [find_path_from_list(path_tuple, default_is_ok) for path_tuple in salt_and_akd_paths[1:]]
    # auth_path = find_path_from_list(salt_and_akd_paths[1], default_is_ok)
    # keys_path = find_path_from_list(salt_and_akd_paths[2], default_is_ok)
    # data_path = find_path_from_list(salt_and_akd_paths[3], default_is_ok)
    if db_paths[0] and db_paths[1] and db_paths[2]:
        paths = []
        exists = True
        for path, i in db_paths:
            # indices.append(i)
            paths.append(path)
        auth_path, keys_path, data_path = tuple(paths)
    else:
        # if a db is not found revert to default filepaths
        auth_path = Path(file_handling_filename).parent / salt_and_akd_paths[1][0]
        if not auth_path.parent.exists():
            auth_path.parent.mkdir(parents=True, exist_ok=True)
        keys_path = Path(file_handling_filename).parent / salt_and_akd_paths[2][0]
        if not keys_path.parent.exists():
            keys_path.parent.mkdir(parents=True, exist_ok=True)
        data_path = Path(file_handling_filename).parent / salt_and_akd_paths[3][0]
        if not data_path.parent.exists():
            data_path.parent.mkdir(parents=True, exist_ok=True)
        # indices += [0, 0, 0]
    # exists = auth_path.exists() and keys_path.exists() and data_path.exists()
    return ((salt, auth_path, keys_path, data_path), exists and salt_exists)  #, tuple(indices))
    