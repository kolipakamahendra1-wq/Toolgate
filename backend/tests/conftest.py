import dataclasses
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.services import build_services  # noqa: E402


@pytest.fixture()
def svc(tmp_path):
    settings = dataclasses.replace(get_settings(), data_dir=tmp_path, embed_provider="hash")
    return build_services(settings)
