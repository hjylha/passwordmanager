'''Add parent folder to paths where Python checks for modules'''

import sys
from pathlib import Path

parent_folder_path = Path(__file__).parent.resolve().parent
sys.path.append(str(parent_folder_path))