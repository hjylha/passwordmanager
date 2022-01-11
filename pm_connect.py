from typing import Optional

from dbs import DB_auth, DB_keys, DB_password
from pm_class import PM
from file_handling import get_files
import file_locations as fl


# def check_filepaths(default_is_ok: bool = True) -> bool:
#     filepaths, exists, _ = get_files(fl.paths, default_is_ok)


def connect_to_pm_dbs(default_is_ok: bool =True, force_connect: bool =False) -> Optional[PM]:
    filepaths, exists = get_files(fl.paths, default_is_ok)
    if exists or force_connect:
        return PM(filepaths[0], DB_auth(filepaths[1]), DB_keys(filepaths[2]), DB_password(filepaths[3]))
    return None

