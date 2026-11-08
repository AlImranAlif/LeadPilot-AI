import os
import tempfile
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    os.environ['DATABASE_URL'] = 'sqlite:///' + path
    os.environ['EXTRACTION_PROVIDER'] = 'demo'
    os.environ['API_KEY'] = ''
    from app.config import get_settings
    get_settings.cache_clear()
    # Reload modules so the database engine is built with test configuration.
    import importlib
    import app.database as database
    import app.models as models
    import app.main as main
    importlib.reload(database)
    importlib.reload(models)
    importlib.reload(main)
    with TestClient(main.app) as c:
        yield c
    os.unlink(path)
