from pathlib import Path

import fix_imports
from dbs import DB_general
import pm_connect as pmc



def test_connect_to_pm_dbs():
    # at the moment only default paths are in file_locations
    assert pmc.connect_to_pm_dbs(False, False) is None

    # make sure the default paths exist, so that we can connect to them
    paths = pmc.get_files(pmc.fl.paths)[0][1:]
    removable = []
    for path in paths:
        if not path.exists():
            removable.append(path)
            DB_general(path)
    assert isinstance(pmc.connect_to_pm_dbs(), pmc.PM)

    # remove files if necessary
    for path in removable:
        path.unlink()

