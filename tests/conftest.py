import pytest
from fastapi.testclient import TestClient
from src.api.main import app

@pytest.fixture
def client():
    """テスト用のAPIクライアント"""
    return TestClient(app)