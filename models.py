from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)  # 邮箱改为可空
    phone = Column(String, unique=True, index=True, nullable=True)  # 手机号改为可空（第三方登录可能没有手机号）
    hashed_password = Column(String, nullable=True)  # 密码改为可空（验证码登录不需要密码）
    avatar = Column(String, nullable=True)
    is_vip = Column(Boolean, default=False)
    vip_expire_date = Column(DateTime, nullable=True)
    merit_points = Column(Integer, default=0)
    # 第三方登录备份字段
    backup_phone = Column(String, nullable=True, index=True)  # 备份手机号，用于第三方登录用户绑定手机号
    login_type = Column(String, default="phone")  # 登录类型：phone, apple, wechat
    is_phone_verified = Column(Boolean, default=False)  # 手机号是否已验证
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class VerificationCode(Base):
    """验证码存储表"""
    __tablename__ = "verification_codes"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, index=True)
    code = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime)  # 过期时间
    used = Column(Boolean, default=False)  # 是否已使用

class UserStat(Base):
    __tablename__ = "user_stats"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_taps = Column(Integer, default=0)
    today_taps = Column(Integer, default=0)
    consecutive_days = Column(Integer, default=0)
    last_tap_date = Column(DateTime, nullable=True)
    user = relationship("User")

class MeditationSession(Base):
    __tablename__ = "meditation_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    duration = Column(Integer)  # 秒
    tap_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User")

class Achievement(Base):
    __tablename__ = "achievements"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    icon = Column(String)

class UserAchievement(Base):
    __tablename__ = "user_achievements"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    achievement_id = Column(Integer, ForeignKey("achievements.id"))
    unlocked_at = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User")
    achievement = relationship("Achievement")

class Leaderboard(Base):
    __tablename__ = "leaderboard"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    period = Column(String)  # daily, weekly
    rank = Column(Integer)
    tap_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User")

class ShareTask(Base):
    __tablename__ = "share_tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    merit = Column(Integer)
    icon = Column(String)

class UserShareTask(Base):
    __tablename__ = "user_share_tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    task_id = Column(Integer, ForeignKey("share_tasks.id"))
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    user = relationship("User")
    task = relationship("ShareTask")

class ThirdPartyAuth(Base):
    """第三方认证信息表"""
    __tablename__ = "third_party_auth"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    platform = Column(String, index=True)  # apple, wechat
    platform_user_id = Column(String, index=True)  # 第三方平台的用户ID
    access_token = Column(String, nullable=True)  # 访问令牌
    refresh_token = Column(String, nullable=True)  # 刷新令牌
    expires_at = Column(DateTime, nullable=True)  # 令牌过期时间
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    user = relationship("User")