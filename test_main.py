"""
WoodenFis Server 自动化测试套件
包含API接口测试、数据库测试、业务逻辑测试
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from faker import Faker
import json
import random
from datetime import datetime, timedelta

from main import app
from database import SessionLocal, engine, Base
from models import User, MeditationSession, Achievement, UserAchievement
import crud
import schemas

fake = Faker('zh_CN')

# 测试数据库设置
@pytest.fixture(scope="session")
def test_db():
    """创建测试数据库表"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """创建数据库会话"""
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
    """创建测试客户端"""
    return TestClient(app)

@pytest.fixture
async def async_client():
    """创建异步测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestUserAPI:
    """用户API测试"""
    
    def test_create_user_success(self, client, db_session):
        """测试用户创建成功"""
        user_data = {
            "username": fake.user_name(),
            "email": fake.email(),
            "password": fake.password()
        }
        
        response = client.post("/users/", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "id" in data
        assert "password" not in data  # 密码不应该返回
    
    def test_create_user_duplicate_email(self, client, db_session):
        """测试重复邮箱用户创建失败"""
        user_data = {
            "username": fake.user_name(),
            "email": "duplicate@test.com",
            "password": fake.password()
        }
        
        # 第一次创建
        response1 = client.post("/users/", json=user_data)
        assert response1.status_code == 200
        
        # 第二次创建相同邮箱
        user_data["username"] = fake.user_name()  # 不同用户名
        response2 = client.post("/users/", json=user_data)
        assert response2.status_code == 400
    
    def test_get_user_by_id(self, client, db_session):
        """测试根据ID获取用户信息"""
        # 先创建用户
        user_data = {
            "username": fake.user_name(),
            "email": fake.email(),
            "password": fake.password()
        }
        create_response = client.post("/users/", json=user_data)
        user_id = create_response.json()["id"]
        
        # 获取用户信息
        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == user_id
        assert data["username"] == user_data["username"]
    
    def test_get_nonexistent_user(self, client):
        """测试获取不存在的用户"""
        response = client.get("/users/99999")
        assert response.status_code == 404


class TestMeditationAPI:
    """冥想API测试"""
    
    @pytest.fixture
    def test_user(self, client):
        """创建测试用户"""
        user_data = {
            "username": fake.user_name(),
            "email": fake.email(),
            "password": fake.password()
        }
        response = client.post("/users/", json=user_data)
        return response.json()
    
    def test_create_meditation_session(self, client, test_user):
        """测试创建冥想会话"""
        session_data = {
            "user_id": test_user["id"],
            "duration": 300,  # 5分钟
            "tap_count": 108,
            "session_type": "木鱼",
            "notes": "测试冥想会话"
        }
        
        response = client.post("/meditation/", json=session_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["user_id"] == test_user["id"]
        assert data["duration"] == 300
        assert data["tap_count"] == 108
    
    def test_get_user_meditation_stats(self, client, test_user):
        """测试获取用户冥想统计"""
        # 创建几个冥想会话
        for _ in range(3):
            session_data = {
                "user_id": test_user["id"],
                "duration": random.randint(60, 600),
                "tap_count": random.randint(10, 200),
                "session_type": "木鱼"
            }
            client.post("/meditation/", json=session_data)
        
        # 获取统计数据
        response = client.get(f"/meditation/stats/{test_user['id']}")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_sessions" in data
        assert "total_duration" in data
        assert "total_taps" in data
        assert data["total_sessions"] == 3


class TestAchievementAPI:
    """成就API测试"""
    
    @pytest.fixture
    def test_user(self, client):
        """创建测试用户"""
        user_data = {
            "username": fake.user_name(),
            "email": fake.email(),
            "password": fake.password()
        }
        response = client.post("/users/", json=user_data)
        return response.json()
    
    def test_get_achievements(self, client):
        """测试获取所有成就"""
        response = client.get("/achievements/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_user_achievements(self, client, test_user):
        """测试获取用户成就"""
        response = client.get(f"/achievements/user/{test_user['id']}")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)


class TestLeaderboardAPI:
    """排行榜API测试"""
    
    def test_get_leaderboard(self, client):
        """测试获取排行榜"""
        response = client.get("/leaderboard/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)


class TestShareAPI:
    """分享API测试"""
    
    @pytest.fixture
    def test_user(self, client):
        """创建测试用户"""
        user_data = {
            "username": fake.user_name(),
            "email": fake.email(),
            "password": fake.password()
        }
        response = client.post("/users/", json=user_data)
        return response.json()
    
    def test_create_share(self, client, test_user):
        """测试创建分享"""
        share_data = {
            "user_id": test_user["id"],
            "content": "今天的冥想很棒！",
            "share_type": "meditation_stats"
        }
        
        response = client.post("/share/", json=share_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["user_id"] == test_user["id"]
        assert data["content"] == share_data["content"]


class TestDatabaseOperations:
    """数据库操作测试"""
    
    def test_crud_create_user(self, db_session):
        """测试CRUD创建用户"""
        user_data = schemas.UserCreate(
            username=fake.user_name(),
            email=fake.email(),
            password=fake.password()
        )
        
        db_user = crud.create_user(db_session, user_data)
        assert db_user.username == user_data.username
        assert db_user.email == user_data.email
        assert db_user.id is not None
    
    def test_crud_get_user(self, db_session):
        """测试CRUD获取用户"""
        # 创建用户
        user_data = schemas.UserCreate(
            username=fake.user_name(),
            email=fake.email(),
            password=fake.password()
        )
        created_user = crud.create_user(db_session, user_data)
        
        # 获取用户
        retrieved_user = crud.get_user(db_session, created_user.id)
        assert retrieved_user.id == created_user.id
        assert retrieved_user.username == created_user.username


class TestBusinessLogic:
    """业务逻辑测试"""
    
    def test_achievement_unlock_logic(self, db_session):
        """测试成就解锁逻辑"""
        # 创建用户
        user_data = schemas.UserCreate(
            username=fake.user_name(),
            email=fake.email(),
            password=fake.password()
        )
        user = crud.create_user(db_session, user_data)
        
        # 创建足够的冥想会话来解锁成就
        for i in range(10):
            session_data = schemas.MeditationSessionCreate(
                user_id=user.id,
                duration=300,
                tap_count=108,
                session_type="木鱼"
            )
            crud.create_meditation_session(db_session, session_data)
        
        # 检查是否解锁了相应成就
        user_achievements = crud.get_user_achievements(db_session, user.id)
        # 这里需要根据实际的成就解锁逻辑来验证


@pytest.mark.asyncio
class TestAsyncOperations:
    """异步操作测试"""
    
    async def test_concurrent_user_creation(self, async_client):
        """测试并发用户创建"""
        async def create_user():
            user_data = {
                "username": fake.user_name(),
                "email": fake.email(),
                "password": fake.password()
            }
            response = await async_client.post("/users/", json=user_data)
            return response
        
        # 并发创建多个用户
        tasks = [create_user() for _ in range(5)]
        responses = await asyncio.gather(*tasks)
        
        # 验证所有用户都创建成功
        for response in responses:
            assert response.status_code == 200


class TestPerformance:
    """性能测试"""
    
    def test_api_response_time(self, client):
        """测试API响应时间"""
        import time
        
        start_time = time.time()
        response = client.get("/achievements/")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # 响应时间小于1秒
    
    def test_bulk_data_handling(self, client):
        """测试批量数据处理"""
        # 创建大量用户
        users = []
        for _ in range(50):
            user_data = {
                "username": fake.user_name(),
                "email": fake.email(),
                "password": fake.password()
            }
            response = client.post("/users/", json=user_data)
            if response.status_code == 200:
                users.append(response.json())
        
        # 验证系统可以处理大量数据
        assert len(users) > 0
        
        # 获取排行榜（可能包含大量数据）
        response = client.get("/leaderboard/")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--html=test_report.html",
        "--cov=.",
        "--cov-report=html",
        "--cov-report=term-missing"
    ]) 