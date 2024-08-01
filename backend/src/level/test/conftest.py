
import pytest
from dotenv import load_dotenv  # type: ignore
from fastapi import FastAPI
from fastapi.testclient import TestClient

from common.logger import log
from level.level_settings import LevelSettings
from level.main_api import app as application
from level.service.aws.levels_ddb import LevelsDdb

# import logging

@pytest.fixture
def app() -> FastAPI:
    application.dependency_overrides = {}

    return application


@pytest.fixture
def client(app : FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture(scope='session', autouse=True)
def load_env():
    load_dotenv()


@pytest.fixture(scope="session")
def test_tables():
    
    settings = LevelSettings.load()
    
    # settings.new_test_session()

    levels_ddb = LevelsDdb(settings)

    log.info(f"TEST TABLES - FIXTURE START")

    if not levels_ddb.create_tables():
        log.warning("Initialization failed")
        return False

    yield test_tables
    
    if not levels_ddb.delete_tables():
        log.warning("Cleanup failed")
        return False

    log.info(f"TEST TABLES - FIXTURE END")

    return True    
