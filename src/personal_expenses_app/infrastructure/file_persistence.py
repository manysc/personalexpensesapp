import os
from pathlib import Path

import pandas as pd


class FilePersistence:
    def __init__(self):
        super().__init__()

    @staticmethod
    def load_corrections(filename=None):
        if filename is None:
            # Use absolute path based on this file's location
            project_root = Path(__file__).parent.parent.parent.parent
            filename = str(project_root / "resources" / "corrections.csv")

        if os.path.exists(filename):
            return pd.read_csv(filename)
        else:
            return pd.DataFrame(columns=["Description", "Category"])

    @staticmethod
    def save_corrections(corrections, filename=None):
        if filename is None:
            # Use absolute path based on this file's location
            project_root = Path(__file__).parent.parent.parent.parent
            filename = str(project_root / "resources" / "corrections.csv")

        if os.path.exists(filename):
            prev = pd.read_csv(filename)
            all_corr = pd.concat(
                [prev, corrections], ignore_index=True
            ).drop_duplicates(subset=["Description", "Category"])
        else:
            all_corr = corrections
        all_corr.to_csv(filename, index=False)
