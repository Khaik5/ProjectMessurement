from __future__ import annotations

import io

import pandas as pd
from fastapi import UploadFile


async def upload_to_dataframe(file: UploadFile) -> pd.DataFrame:
    content = await file.read()
    filename = file.filename or ""
    suffix = filename.rsplit(".", 1)[-1].lower()
    if suffix == "csv":
        return pd.read_csv(io.BytesIO(content))
    if suffix == "json":
        return pd.read_json(io.BytesIO(content))
    raise ValueError("Only CSV and JSON datasets are supported")
