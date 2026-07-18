import io

import pandas as pd

from personal_expenses_app.infrastructure.s3_storage import get_object_bytes, put_object_bytes

_CORRECTIONS_KEY = "resources/corrections.csv"


class FilePersistence:
    def __init__(self):
        super().__init__()

    @staticmethod
    def load_corrections(filename=None):
        """`filename` is an S3 object key; defaults to `resources/corrections.csv`."""
        key = filename or _CORRECTIONS_KEY
        try:
            return pd.read_csv(io.BytesIO(get_object_bytes(key)))
        except FileNotFoundError:
            return pd.DataFrame(columns=["Description", "Category"])

    @staticmethod
    def save_corrections(corrections, filename=None):
        """`filename` is an S3 object key; defaults to `resources/corrections.csv`."""
        key = filename or _CORRECTIONS_KEY
        try:
            prev = pd.read_csv(io.BytesIO(get_object_bytes(key)))
            all_corr = pd.concat(
                [prev, corrections], ignore_index=True
            ).drop_duplicates(subset=["Description", "Category"])
        except FileNotFoundError:
            all_corr = corrections
        put_object_bytes(key, all_corr.to_csv(index=False).encode("utf-8"))

