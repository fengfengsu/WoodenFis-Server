"""
手机号验证码登录功能测试

测试新增的手机号验证码登录API功能：
- 发送验证码API测试
- 验证码登录API测试
- 用户自动创建测试
"""

import pytest
from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

class TestPhoneLogin:
    """手机号验证码登录测试类"""
    
    def test_send_verification_code_success(self):
        """测试发送验证码成功"""
        response = client.post(
            "/users/send-code",
            json={"phone": "13800138000"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "验证码已发送" in data["message"]
        
    def test_send_verification_code_invalid_phone(self):
        """测试发送验证码 - 手机号格式错误"""
        response = client.post(
            "/users/send-code",
            json={"phone": "12345"}
        )
        assert response.status_code == 400
        assert "手机号格式不正确" in response.json()["detail"]
        
    def test_login_with_verification_code_new_user(self):
        """测试验证码登录 - 新用户自动创建"""
        # 先发送验证码
        phone = "13900139000"
        send_response = client.post(
            "/users/send-code",
            json={"phone": phone}
        )
        assert send_response.status_code == 200
        
        # 从响应中提取验证码（仅用于测试）
        message = send_response.json()["message"]
        code = message.split("测试用验证码: ")[1]
        
        # 使用验证码登录
        login_response = client.post(
            "/users/login",
            json={"phone": phone, "code": code}
        )
        assert login_response.status_code == 200
        data = login_response.json()
        assert data["message"] == "登录成功"
        assert data["user"]["phone"] == phone
        assert data["user"]["username"].startswith("用户")
        
    def test_login_with_invalid_code(self):
        """测试验证码登录 - 无效验证码"""
        response = client.post(
            "/users/login",
            json={"phone": "13800138000", "code": "000000"}
        )
        assert response.status_code == 400
        assert "验证码无效或已过期" in response.json()["detail"]
        
    def test_login_with_used_code(self):
        """测试验证码登录 - 已使用的验证码"""
        phone = "13700137000"
        
        # 发送验证码
        send_response = client.post(
            "/users/send-code",
            json={"phone": phone}
        )
        code = send_response.json()["message"].split("测试用验证码: ")[1]
        
        # 第一次使用验证码登录
        client.post("/users/login", json={"phone": phone, "code": code})
        
        # 再次使用相同验证码登录，应该失败
        response = client.post(
            "/users/login",
            json={"phone": phone, "code": code}
        )
        assert response.status_code == 400
        assert "验证码无效或已过期" in response.json()["detail"]

if __name__ == "__main__":
    """运行测试"""
    test = TestPhoneLogin()
    
    print("🧪 开始测试手机号验证码登录功能...")
    
    try:
        test.test_send_verification_code_success()
        print("✅ 发送验证码测试通过")
        
        test.test_send_verification_code_invalid_phone()
        print("✅ 无效手机号测试通过")
        
        test.test_login_with_verification_code_new_user()
        print("✅ 新用户验证码登录测试通过")
        
        test.test_login_with_invalid_code()
        print("✅ 无效验证码测试通过")
        
        test.test_login_with_used_code()
        print("✅ 重复使用验证码测试通过")
        
        print("🎉 所有测试通过！手机号验证码登录功能正常工作")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}") 