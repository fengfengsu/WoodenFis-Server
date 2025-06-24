import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
from database import get_db, engine
from models import Base, VerificationCode
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import json

# 创建测试数据库
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# 创建所有表
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_rate_limit():
    phone = "13800138000"
    
    # 清理数据库
    db = TestingSessionLocal()
    db.query(VerificationCode).filter(VerificationCode.phone == phone).delete()
    db.commit()
    
    print(f"测试手机号: {phone}")
    
    # 第一次发送验证码
    print("\n=== 第一次发送验证码 ===")
    response1 = client.post("/api/send-code", json={"phone": phone})
    print(f"状态码: {response1.status_code}")
    print(f"响应: {response1.json()}")
    
    # 检查数据库中的验证码记录
    codes = db.query(VerificationCode).filter(VerificationCode.phone == phone).all()
    print(f"\n数据库中的验证码记录数: {len(codes)}")
    for i, code in enumerate(codes):
        print(f"记录 {i+1}: code={code.code}, used={code.used}, created_at={code.created_at}, expires_at={code.expires_at}")
    
    # 立即第二次发送验证码（应该被限流）
    print("\n=== 立即第二次发送验证码 ===")
    response2 = client.post("/api/send-code", json={"phone": phone})
    print(f"状态码: {response2.status_code}")
    print(f"响应: {response2.json()}")
    
    # 再次检查数据库
    codes = db.query(VerificationCode).filter(VerificationCode.phone == phone).all()
    print(f"\n数据库中的验证码记录数: {len(codes)}")
    for i, code in enumerate(codes):
        print(f"记录 {i+1}: code={code.code}, used={code.used}, created_at={code.created_at}, expires_at={code.expires_at}")
    
    db.close()
    
    return response1.status_code, response2.status_code

if __name__ == "__main__":
    status1, status2 = test_rate_limit()
    print(f"\n=== 测试结果 ===")
    print(f"第一次发送状态码: {status1} (期望: 200)")
    print(f"第二次发送状态码: {status2} (期望: 429)")
    
    if status1 == 200 and status2 == 429:
        print("✅ 限流测试通过")
    else:
        print("❌ 限流测试失败")