import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from main import app
from database import get_db
import models
import crud

# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_sms.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(setup_database):
    return TestClient(app)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

class TestSMSService:
    """短信服务测试类"""
    
    def test_send_verification_code_success(self, client):
        """测试成功发送验证码"""
        with patch('sms_service.sms_service.send_verification_code') as mock_send:
            mock_send.return_value = {
                'success': True,
                'message': '验证码已发送',
                'code': 'OK',
                'request_id': 'test_request_id'
            }
            
            response = client.post("/users/send-code", json={
                "phone": "13800138000"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "验证码已发送" in data["message"]
    
    def test_send_verification_code_invalid_phone(self, client):
        """测试无效手机号"""
        response = client.post("/users/send-code", json={
            "phone": "12345"
        })
        
        assert response.status_code == 400
        assert "手机号格式不正确" in response.json()["detail"]
    
    def test_send_verification_code_rate_limit(self, client, db_session):
        """测试5分钟内重复发送限制"""
        phone = "13800138001"
        
        # 先创建一个5分钟内的验证码记录
        code_record = models.VerificationCode(
            phone=phone,
            code="123456",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            used=False
        )
        db_session.add(code_record)
        db_session.commit()
        
        # 尝试再次发送
        response = client.post("/users/send-code", json={
            "phone": phone
        })
        
        assert response.status_code == 429
        assert "请等待5分钟后再次发送验证码" in response.json()["detail"]
    
    def test_send_verification_code_sms_failure(self, client):
        """测试短信发送失败"""
        with patch('sms_service.sms_service.send_verification_code') as mock_send:
            mock_send.return_value = {
                'success': False,
                'message': '短信发送失败',
                'code': 'ERROR',
                'request_id': None
            }
            
            response = client.post("/users/send-code", json={
                "phone": "13800138002"
            })
            
            assert response.status_code == 500
            assert "短信发送失败" in response.json()["detail"]
    
    def test_login_with_valid_code(self, client, db_session):
        """测试使用有效验证码登录"""
        phone = "13800138003"
        code = "123456"
        
        # 创建有效的验证码记录
        code_record = models.VerificationCode(
            phone=phone,
            code=code,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            used=False
        )
        db_session.add(code_record)
        db_session.commit()
        
        response = client.post("/users/login", json={
            "phone": phone,
            "code": code
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "登录成功" in data["message"]
        assert data["user"]["phone"] == phone
    
    def test_login_with_invalid_code(self, client):
        """测试使用无效验证码登录"""
        response = client.post("/users/login", json={
            "phone": "13800138004",
            "code": "000000"
        })
        
        assert response.status_code == 400
        assert "验证码无效或已过期" in response.json()["detail"]
    
    def test_login_with_expired_code(self, client, db_session):
        """测试使用过期验证码登录"""
        phone = "13800138005"
        code = "123456"
        
        # 创建过期的验证码记录
        code_record = models.VerificationCode(
            phone=phone,
            code=code,
            created_at=datetime.utcnow() - timedelta(minutes=10),
            expires_at=datetime.utcnow() - timedelta(minutes=5),
            used=False
        )
        db_session.add(code_record)
        db_session.commit()
        
        response = client.post("/users/login", json={
            "phone": phone,
            "code": code
        })
        
        assert response.status_code == 400
        assert "验证码无效或已过期" in response.json()["detail"]
    
    def test_can_send_verification_code(self, db_session):
        """测试验证码发送限制检查函数"""
        phone = "13800138006"
        
        # 没有记录时应该可以发送
        assert crud.can_send_verification_code(db_session, phone) is True
        
        # 创建5分钟内的记录
        code_record = models.VerificationCode(
            phone=phone,
            code="123456",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
        db_session.add(code_record)
        db_session.commit()
        
        # 5分钟内不应该可以发送
        assert crud.can_send_verification_code(db_session, phone) is False
        
        # 删除旧记录，创建6分钟前的记录
        db_session.delete(code_record)
        db_session.commit()
        
        old_code_record = models.VerificationCode(
            phone=phone,
            code="123456",
            created_at=datetime.utcnow() - timedelta(minutes=6),
            expires_at=datetime.utcnow() - timedelta(minutes=1)
        )
        db_session.add(old_code_record)
        db_session.commit()
        
        # 6分钟后应该可以发送
        assert crud.can_send_verification_code(db_session, phone) is True

if __name__ == "__main__":
    pytest.main(["-v", __file__])