from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None  # 邮箱改为可选
    phone: str  # 添加手机号字段
    avatar: Optional[str] = None

class UserCreate(UserBase):
    password: Optional[str] = None  # 密码改为可选

class UserCreateByPhone(BaseModel):
    """通过手机号创建用户"""
    username: str
    phone: str
    avatar: Optional[str] = None

class SendCodeRequest(BaseModel):
    """发送验证码请求"""
    phone: str

class VerifyCodeRequest(BaseModel):
    """验证码登录请求"""
    phone: str
    code: str

class SendCodeResponse(BaseModel):
    """发送验证码响应"""
    message: str
    success: bool

class LoginResponse(BaseModel):
    """登录响应"""
    user: 'UserOut'
    token: Optional[str] = None  # 如果需要JWT token
    message: str

class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    is_vip: bool
    vip_expire_date: Optional[datetime] = None
    merit_points: int
    backup_phone: Optional[str] = None
    login_type: str
    is_phone_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserStatOut(BaseModel):
    total_taps: int
    today_taps: int
    consecutive_days: int
    last_tap_date: Optional[datetime]

    class Config:
        from_attributes = True

class MeditationSessionCreate(BaseModel):
    duration: int
    tap_count: int

class MeditationSessionOut(MeditationSessionCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class AchievementOut(BaseModel):
    id: int
    name: str
    description: str
    icon: str

    class Config:
        from_attributes = True

class UserAchievementOut(BaseModel):
    achievement: AchievementOut
    unlocked_at: datetime

    class Config:
        from_attributes = True

class LeaderboardOut(BaseModel):
    user_id: int
    period: str
    rank: int
    tap_count: int
    created_at: datetime
    username: str

    class Config:
        from_attributes = True

class ShareTaskOut(BaseModel):
    id: int
    title: str
    description: str
    merit: int

# Apple认证相关
class AppleLoginRequest(BaseModel):
    """Apple登录请求"""
    identity_token: str
    authorization_code: str
    user_identifier: str
    full_name: Optional[str] = None
    email: Optional[str] = None

class AppleLoginResponse(BaseModel):
    """Apple登录响应"""
    user: 'UserOut'
    token: Optional[str] = None
    message: str
    is_new_user: bool

# 微信认证相关
class WeChatLoginRequest(BaseModel):
    """微信登录请求"""
    code: str  # 微信授权码
    
class WeChatLoginResponse(BaseModel):
    """微信登录响应"""
    user: 'UserOut'
    token: Optional[str] = None
    message: str
    is_new_user: bool

# 第三方用户信息
class ThirdPartyUserInfo(BaseModel):
    """第三方用户信息"""
    platform: str
    platform_user_id: str
    username: str
    email: Optional[str] = None
    avatar: Optional[str] = None
    icon: Optional[str] = None

    class Config:
        from_attributes = True

class UserShareTaskOut(BaseModel):
    task: ShareTaskOut
    completed: bool
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True