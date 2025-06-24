"""
pytest配置文件
定义全局fixture和测试配置
"""

import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from httpx import AsyncClient
from faker import Faker
import asyncio

from main import app
from database import Base, engine, SessionLocal, get_db
from models import User, MeditationSession, Achievement, UserAchievement
import crud
import schemas

fake = Faker('zh_CN')

# 测试数据库URL
TEST_DATABASE_URL = "sqlite:///./test_woodenfish.db"

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """设置测试数据库"""
    # 创建测试表
    Base.metadata.create_all(bind=engine)
    yield
    # 清理测试数据库
    Base.metadata.drop_all(bind=engine)
    # 删除测试数据库文件
    if os.path.exists("test_woodenfish.db"):
        os.remove("test_woodenfish.db")

@pytest.fixture
def db():
    """提供数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        # 清理测试数据
        db.query(UserAchievement).delete()
        db.query(MeditationSession).delete() 
        db.query(User).delete()
        db.commit()
        db.close()

@pytest.fixture
def client():
    """提供测试客户端"""
    return TestClient(app)

@pytest.fixture
async def async_client():
    """提供异步测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sample_user_data():
    """提供示例用户数据"""
    return {
        "username": fake.user_name(),
        "email": fake.email(),
        "password": fake.password()
    }

@pytest.fixture
def created_user(client, sample_user_data):
    """创建测试用户"""
    response = client.post("/users/", json=sample_user_data)
    if response.status_code == 200:
        return response.json()
    return None

@pytest.fixture
def sample_meditation_data(created_user):
    """提供示例冥想数据"""
    if created_user:
        return {
            "user_id": created_user["id"],
            "duration": 300,
            "tap_count": 108,
            "session_type": "木鱼",
            "notes": "测试冥想会话"
        }
    return None

@pytest.fixture
def multiple_users(client):
    """创建多个测试用户"""
    users = []
    for _ in range(5):
        user_data = {
            "username": fake.user_name(),
            "email": fake.email(),
            "password": fake.password()
        }
        response = client.post("/users/", json=user_data)
        if response.status_code == 200:
            users.append(response.json())
    return users

@pytest.fixture
def meditation_sessions(client, created_user):
    """创建多个冥想会话"""
    sessions = []
    if created_user:
        for i in range(3):
            session_data = {
                "user_id": created_user["id"],
                "duration": 300 + i * 60,
                "tap_count": 108 + i * 10,
                "session_type": "木鱼"
            }
            response = client.post("/meditation/", json=session_data)
            if response.status_code == 200:
                sessions.append(response.json())
    return sessions

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """为所有测试启用数据库访问"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()

# 测试标记配置
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试") 
    config.addinivalue_line("markers", "api: API测试")
    config.addinivalue_line("markers", "database: 数据库测试")
    config.addinivalue_line("markers", "performance: 性能测试")
    config.addinivalue_line("markers", "slow: 慢速测试")

def pytest_collection_modifyitems(config, items):
    """修改测试项目集合"""
    for item in items:
        # 为数据库相关测试添加标记
        if "database" in item.nodeid or "crud" in item.nodeid:
            item.add_marker(pytest.mark.database)
        
        # 为API相关测试添加标记
        if "api" in item.nodeid or "test_" in item.name and "API" in item.name:
            item.add_marker(pytest.mark.api)
        
        # 为性能测试添加标记
        if "performance" in item.nodeid or "perf" in item.nodeid:
            item.add_marker(pytest.mark.performance)

@pytest.fixture
def mock_external_api(monkeypatch):
    """模拟外部API"""
    def mock_request(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200
                self.text = '{"success": true}'
            
            def json(self):
                return {"success": True, "data": "mocked"}
        
        return MockResponse()
    
    monkeypatch.setattr("requests.get", mock_request)
    monkeypatch.setattr("requests.post", mock_request)

@pytest.fixture
def temp_file():
    """创建临时文件"""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        yield f.name
    os.unlink(f.name)

# 性能测试相关fixture
@pytest.fixture
def performance_threshold():
    """性能测试阈值"""
    return {
        "api_response_time": 1.0,  # 秒
        "database_query_time": 0.5,  # 秒
        "memory_usage": 100,  # MB
    } 