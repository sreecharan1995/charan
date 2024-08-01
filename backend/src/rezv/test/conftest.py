import pytest
from dotenv import load_dotenv # type: ignore
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rezv.main_api import app as application


@pytest.fixture
def app() -> FastAPI:
    application.dependency_overrides = {}
    return application


@pytest.fixture
def client(app) -> TestClient: # type: ignore
    return TestClient(app) # type: ignore


@pytest.fixture(scope='session', autouse=True)
def load_env():
    load_dotenv()
