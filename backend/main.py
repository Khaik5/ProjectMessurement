"""Compatibility ASGI entrypoint.

The canonical command is:

    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

This module keeps ``uvicorn main:app`` working when it is run from the
``backend`` directory, so an old command does not fail with
``Could not import module "main"``.
"""

from app.main import app

