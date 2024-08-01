

## from cgi import test
import pytest
# from pytest import param
from dotenv import load_dotenv  # type: ignore
from fastapi import FastAPI
from fastapi.testclient import TestClient

from common.logger import log
from configs.configs_settings import ConfigsSettings
from configs.main_api import app as application
from configs.service.aws.configs_ddb import ConfigsDdb


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
    
    settings = ConfigsSettings.load_configs()
    
    configs_ddb = ConfigsDdb(settings=settings)

    log.info(f"TEST TABLES - FIXTURE START")

    if not configs_ddb.create_tables():
        log.warning("Initialization failed")
        return False

    yield test_tables
    
    if not configs_ddb.delete_tables():
        log.warning("Cleanup failed")
        return False

    log.info(f"TEST TABLES - FIXTURE END")

    return True        
    
