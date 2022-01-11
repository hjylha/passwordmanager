from pathlib import Path

import fix_imports
import pm_connect as pmc


def test_connect_to_pm_dbs():
    assert pmc.connect_to_pm_dbs(False, False) is None

    assert isinstance(pmc.connect_to_pm_dbs(), pmc.PM)
