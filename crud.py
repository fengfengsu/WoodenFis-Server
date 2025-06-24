from sqlalchemy.orm import Session
import models, schemas
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import Column, desc

# 用户相关

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_phone(db: Session, phone: str) -> Optional[models.User]:
    """根据手机号查询用户"""
    return db.query(models.User).filter(models.User.phone == phone).first()

def create_user(db: Session, user: schemas.UserCreate, hashed_password: str) -> models.User:
    db_user = models.User(
        username=user.username,
        email=user.email,
        phone=user.phone,
        hashed_password=hashed_password,
        avatar=user.avatar
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_user_by_phone(db: Session, user: schemas.UserCreateByPhone) -> models.User:
    """通过手机号创建用户（无密码）"""
    db_user = models.User(
        username=user.username,
        phone=user.phone,
        avatar=user.avatar
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# 第三方认证相关

def get_third_party_auth(db: Session, platform: str, platform_user_id: str) -> Optional[models.ThirdPartyAuth]:
    """根据平台和平台用户ID查询第三方认证信息"""
    return db.query(models.ThirdPartyAuth).filter(
        models.ThirdPartyAuth.platform == platform,
        models.ThirdPartyAuth.platform_user_id == platform_user_id
    ).first()

def get_user_by_third_party(db: Session, platform: str, platform_user_id: str) -> Optional[models.User]:
    """根据第三方平台信息查询用户"""
    auth = get_third_party_auth(db, platform, platform_user_id)
    if auth:
        return db.query(models.User).filter(models.User.id == auth.user_id).first()
    return None

def create_third_party_auth(db: Session, user_id: Column, platform: str, platform_user_id: str, 
                           access_token: Optional[str] = None, refresh_token: Optional[str] = None,
                           expires_at: Optional[datetime] = None) -> models.ThirdPartyAuth:
    """创建第三方认证记录"""
    auth = models.ThirdPartyAuth(
        user_id=user_id,
        platform=platform,
        platform_user_id=platform_user_id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at
    )
    db.add(auth)
    db.commit()
    db.refresh(auth)
    return auth

def update_third_party_auth(db: Session, auth_id: Column, update_data: dict):
    """更新第三方认证信息"""
    db_auth = db.query(models.ThirdPartyAuth).filter(models.ThirdPartyAuth.id == auth_id).first()
    if db_auth:
        for key, value in update_data.items():
            if hasattr(db_auth, key):
                setattr(db_auth, key, value)
        db.commit()
        db.refresh(db_auth)
    return db_auth

def update_user_backup_phone(db: Session, user_id: int, backup_phone: str):
    """更新用户备份手机号"""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        setattr(db_user, 'backup_phone', backup_phone)
        db.commit()
        db.refresh(db_user)
    return db_user

def verify_user_phone(db: Session, user_id: int):
    """验证用户手机号"""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        setattr(db_user, 'is_phone_verified', True)
        db.commit()
        db.refresh(db_user)
    return db_user

def get_users_by_login_type(db: Session, login_type: str, skip: int = 0, limit: int = 100):
    """根据登录类型获取用户列表"""
    return db.query(models.User).filter(models.User.login_type == login_type).offset(skip).limit(limit).all()

def bind_phone_to_third_party_user(db: Session, user_id: int, phone: str):
    """为第三方登录用户绑定手机号"""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user and getattr(db_user, 'login_type') in ['apple', 'wechat']:
        # 如果用户已有手机号，将其设为备份手机号
        current_phone = getattr(db_user, 'phone', None)
        if current_phone:
            setattr(db_user, 'backup_phone', current_phone)
        setattr(db_user, 'phone', phone)
        setattr(db_user, 'is_phone_verified', True)
        db.commit()
        db.refresh(db_user)
    return db_user

def create_user_by_third_party(db: Session, user_info: schemas.ThirdPartyUserInfo) -> models.User:
    """通过第三方信息创建用户"""
    db_user = models.User(
        username=user_info.username,
        email=user_info.email,
        avatar=user_info.avatar,
        login_type=user_info.platform,
        is_phone_verified=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# 用户统计

def get_user_stat(db: Session, user_id: int) -> Optional[models.UserStat]:
    return db.query(models.UserStat).filter(models.UserStat.user_id == user_id).first()

def create_user_stat(db: Session, user_id: Column) -> models.UserStat:
    stat = models.UserStat(user_id=user_id)
    db.add(stat)
    db.commit()
    db.refresh(stat)
    return stat

# 冥想会话

def create_meditation_session(db: Session, user_id: int, session: schemas.MeditationSessionCreate) -> models.MeditationSession:
    db_session = models.MeditationSession(
        user_id=user_id,
        duration=session.duration,
        tap_count=session.tap_count
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_meditation_sessions(db: Session, user_id: int, limit: int = 10) -> List[models.MeditationSession]:
    return db.query(models.MeditationSession).filter(models.MeditationSession.user_id == user_id).order_by(desc(models.MeditationSession.created_at)).limit(limit).all()

# 成就

def get_achievements(db: Session) -> List[models.Achievement]:
    return db.query(models.Achievement).all()

def unlock_achievement(db: Session, user_id: int, achievement_id: int) -> models.UserAchievement:
    ua = models.UserAchievement(user_id=user_id, achievement_id=achievement_id)
    db.add(ua)
    db.commit()
    db.refresh(ua)
    return ua

def get_user_achievements(db: Session, user_id: int) -> List[models.UserAchievement]:
    return db.query(models.UserAchievement).filter(models.UserAchievement.user_id == user_id).all()

# 排行榜

def get_leaderboard(db: Session, period: str, limit: int = 10) -> List[models.Leaderboard]:
    # 使用 join 连接 User 表，以便获取用户名
    return db.query(models.Leaderboard).join(models.User, models.Leaderboard.user_id == models.User.id).filter(models.Leaderboard.period == period).order_by(models.Leaderboard.rank).limit(limit).all()

# 分享任务

def get_share_tasks(db: Session) -> List[models.ShareTask]:
    return db.query(models.ShareTask).all()

def complete_share_task(db: Session, user_id: int, task_id: int) -> models.UserShareTask:
    ust = models.UserShareTask(user_id=user_id, task_id=task_id, completed=True, completed_at=datetime.utcnow())
    db.add(ust)
    db.commit()
    db.refresh(ust)
    return ust

def get_user_share_tasks(db: Session, user_id: int) -> List[models.UserShareTask]:
    return db.query(models.UserShareTask).filter(models.UserShareTask.user_id == user_id).all()

# 验证码相关

def can_send_verification_code(db: Session, phone: str) -> bool:
    """检查是否可以发送验证码（5分钟内只能发送一次）"""
    from datetime import datetime, timedelta
    
    # 检查5分钟内是否已发送过验证码
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    recent_code = db.query(models.VerificationCode).filter(
        models.VerificationCode.phone == phone,
        models.VerificationCode.created_at > five_minutes_ago
    ).first()
    
    return recent_code is None

def create_verification_code(db: Session, phone: str, code: str, expires_at: datetime) -> models.VerificationCode:
    """创建验证码记录"""
    # 先将该手机号之前的验证码标记为已使用
    db.query(models.VerificationCode).filter(
        models.VerificationCode.phone == phone,
        models.VerificationCode.used == False
    ).update({models.VerificationCode.used: True})
    
    db_code = models.VerificationCode(
        phone=phone,
        code=code,
        expires_at=expires_at
    )
    db.add(db_code)
    db.commit()
    db.refresh(db_code)
    return db_code

def get_valid_verification_code(db: Session, phone: str, code: str) -> Optional[models.VerificationCode]:
    """获取有效的验证码"""
    return db.query(models.VerificationCode).filter(
        models.VerificationCode.phone == phone,
        models.VerificationCode.code == code,
        models.VerificationCode.used == False,
        models.VerificationCode.expires_at > datetime.utcnow()
    ).first()

def use_verification_code(db: Session, code_id: Column):
    """标记验证码为已使用"""
    db.query(models.VerificationCode).filter(
        models.VerificationCode.id == code_id
    ).update({models.VerificationCode.used: True})
    db.commit()