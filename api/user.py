from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal, get_db
from typing import List
import random
import string
from datetime import datetime, timedelta
from sms_service import sms_service
from third_party_auth import apple_auth_service, wechat_auth_service
import third_party_auth
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

# 简单的用户认证函数（用于需要认证的接口）
def get_current_user(db: Session = Depends(get_db)) -> models.User:
    """获取当前用户（简化版本，实际项目中应该使用JWT等认证方式）"""
    # 这里是一个简化的实现，实际项目中应该从JWT token或session中获取用户信息
    # 为了修复当前错误，我们暂时返回一个默认用户或抛出异常
    raise HTTPException(status_code=401, detail="需要用户认证")

def generate_verification_code() -> str:
    """生成6位数字验证码"""
    return ''.join(random.choices(string.digits, k=6))

@router.post("/send-code", response_model=schemas.SendCodeResponse)
def send_verification_code(request: schemas.SendCodeRequest, db: Session = Depends(get_db)):
    """
    发送验证码
    """
    # 验证手机号格式
    if not request.phone.startswith('1') or len(request.phone) != 11:
        raise HTTPException(status_code=400, detail="手机号格式不正确")
    
    # 检查5分钟内是否已发送过验证码
    if not crud.can_send_verification_code(db, request.phone):
        raise HTTPException(status_code=429, detail="请等待5分钟后再次发送验证码")
    
    # 生成验证码
    code = generate_verification_code()
    expires_at = datetime.utcnow() + timedelta(minutes=5)  # 5分钟过期
    
    # 发送短信
    sms_result = sms_service.send_verification_code(request.phone, code)
    
    if not sms_result['success']:
        logger.error(f"短信发送失败: {sms_result['message']}")
        raise HTTPException(status_code=500, detail="短信发送失败，请稍后重试")
    
    # 保存验证码到数据库
    crud.create_verification_code(db, request.phone, code, expires_at)
    
    # 根据是否为模拟模式返回不同的消息
    if sms_service.is_configured():
        message = f"验证码已发送到 {request.phone}"
    else:
        # 开发模式下返回验证码（生产环境中绝不能这样做）
        message = f"验证码已发送到 {request.phone}，开发模式验证码: {code}"
    
    return schemas.SendCodeResponse(
        message=message,
        success=True
    )

@router.post("/login", response_model=schemas.LoginResponse)
def login_with_code(request: schemas.VerifyCodeRequest, db: Session = Depends(get_db)):
    """
    验证码登录
    """
    # 验证验证码
    verification_code = crud.get_valid_verification_code(db, request.phone, request.code)
    if not verification_code:
        raise HTTPException(status_code=400, detail="验证码无效或已过期")
    
    # 标记验证码为已使用
    crud.use_verification_code(db, verification_code.id)
    
    # 查找或创建用户
    user = crud.get_user_by_phone(db, request.phone)
    if not user:
        # 如果用户不存在，自动创建新用户
        username = f"用户{request.phone[-4:]}"  # 使用手机号后4位生成用户名
        user_create = schemas.UserCreateByPhone(
            username=username,
            phone=request.phone
        )
        user = crud.create_user_by_phone(db, user_create)
        
        # 为新用户创建统计记录
        crud.create_user_stat(db, user.id)
    
    return schemas.LoginResponse(
        user=user,
        message="登录成功"
    )

@router.post("/apple-login", response_model=schemas.AppleLoginResponse)
def apple_login(request: schemas.AppleLoginRequest, db: Session = Depends(get_db)):
    """
    Apple Sign In 登录
    """
    # 验证Apple身份令牌
    payload = apple_auth_service.verify_identity_token(request.identity_token)
    if not payload:
        raise HTTPException(status_code=400, detail="Apple身份令牌验证失败")
    
    apple_user_id = payload.get('sub')
    email = payload.get('email')
    
    if not apple_user_id:
        raise HTTPException(status_code=400, detail="无法获取Apple用户标识")
    
    # 查找现有用户
    existing_user = crud.get_user_by_third_party(db, 'apple', apple_user_id)
    is_new_user = False
    
    if existing_user:
        user = existing_user
        # 更新第三方认证信息
        auth = crud.get_third_party_auth(db, 'apple', apple_user_id)
        if auth:
            crud.update_third_party_auth(db, auth.id, {})
    else:
        # 创建新用户
        is_new_user = True
        
        # 生成用户名
        username = request.full_name or "Apple用户"
        if not request.full_name:
            username = f"Apple用户{apple_user_id[-6:]}"
        
        # 检查用户名是否已存在
        counter = 1
        original_username = username
        while crud.get_user_by_username(db, username):
            username = f"{original_username}{counter}"
            counter += 1
        
        user_info = schemas.ThirdPartyUserInfo(
            platform='apple',
            platform_user_id=apple_user_id,
            username=username,
            email=email,
            icon=None
        )
        
        user = crud.create_user_by_third_party(db, user_info)
        
        # 创建第三方认证记录
        crud.create_third_party_auth(db, user.id, 'apple', apple_user_id)
        
        # 为新用户创建统计记录
        crud.create_user_stat(db, user.id)
    
    return schemas.AppleLoginResponse(
        user=user,
        message="Apple登录成功",
        is_new_user=is_new_user
    )

@router.post("/wechat-login", response_model=schemas.UserOut)
def wechat_login(user_info: schemas.ThirdPartyUserInfo, db: Session = Depends(get_db)):
    """微信登录"""
    try:
        # 验证微信授权码
        wechat_user_info = wechat_auth_service.verify_wechat_auth(user_info.platform_user_id)
        
        # 查找或创建用户
        user = crud.get_user_by_email(db, wechat_user_info['email']) if wechat_user_info.get('email') else None
        if not user:
            # 创建新用户
            user_create_info = schemas.ThirdPartyUserInfo(
                username=wechat_user_info['nickname'],
                email=wechat_user_info.get('email'),
                avatar=wechat_user_info.get('avatar'),
                platform="wechat",
                platform_user_id=wechat_user_info['openid'],
                # 移除 auth_code 字段，因为 ThirdPartyUserInfo 模型中未定义该字段
                icon=user_info.icon
            )
            user = crud.create_user_by_third_party(db, user_create_info)
        
        # 更新或创建第三方认证信息
        auth = crud.get_third_party_auth(db, "wechat", wechat_user_info['openid'])
        if auth:
            crud.update_third_party_auth(db, auth.id, {
                'access_token': wechat_user_info.get('access_token'),
                'refresh_token': wechat_user_info.get('refresh_token'),
                'updated_at': datetime.utcnow()
            })
        else:
            crud.create_third_party_auth(db, user.id, "wechat", wechat_user_info['openid'], 
                                       wechat_user_info.get('access_token'), 
                                       wechat_user_info.get('refresh_token'))
        
        # 创建用户统计记录
        crud.create_user_stat(db, user.id)
        
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"微信登录失败: {str(e)}")

@router.post("/bind-backup-phone")
async def bind_backup_phone(
    phone_data: dict,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """绑定备份手机号"""
    phone = phone_data.get("phone")
    if not phone:
        raise HTTPException(status_code=400, detail="手机号不能为空")
    
    # 检查手机号格式
    if not re.match(r'^1[3-9]\d{9}$', phone):
        raise HTTPException(status_code=400, detail="手机号格式不正确")
    
    # 检查手机号是否已被其他用户使用
    existing_user = crud.get_user_by_phone(db, phone)
    if existing_user and existing_user.id != getattr(current_user, 'id'):
        raise HTTPException(status_code=400, detail="该手机号已被其他用户使用")
    
    # 更新备份手机号
    updated_user = crud.update_user_backup_phone(db, getattr(current_user, 'id'), phone)
    if not updated_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {"message": "备份手机号绑定成功", "backup_phone": phone}

@router.post("/update-backup-phone")
async def update_backup_phone(
    phone_data: dict,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新备份手机号"""
    phone = phone_data.get("phone")
    if not phone:
        raise HTTPException(status_code=400, detail="手机号不能为空")
    
    # 检查手机号格式
    if not re.match(r'^1[3-9]\d{9}$', phone):
        raise HTTPException(status_code=400, detail="手机号格式不正确")
    
    # 检查手机号是否已被其他用户使用
    existing_user = crud.get_user_by_phone(db, phone)
    if existing_user and existing_user.id != getattr(current_user, 'id'):
        raise HTTPException(status_code=400, detail="该手机号已被其他用户使用")
    
    # 更新备份手机号
    updated_user = crud.update_user_backup_phone(db, getattr(current_user, 'id'), phone)
    if not updated_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {"message": "备份手机号更新成功", "backup_phone": phone}

@router.get("/users-by-login-type")
async def get_users_by_login_type(
    login_type: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """根据登录类型获取用户列表"""
    if login_type not in ['phone', 'apple', 'wechat']:
        raise HTTPException(status_code=400, detail="无效的登录类型")
    
    users = crud.get_users_by_login_type(db, login_type, skip, limit)
    return {
        "login_type": login_type,
        "count": len(users),
        "users": [{
            "id": getattr(user, 'id'),
            "username": getattr(user, 'username'),
            "phone": getattr(user, 'phone'),
            "backup_phone": getattr(user, 'backup_phone'),
            "login_type": getattr(user, 'login_type'),
            "is_phone_verified": getattr(user, 'is_phone_verified'),
            "created_at": getattr(user, 'created_at')
        } for user in users]
    }

@router.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    传统注册方式（保留兼容性）
    """
    db_user = crud.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    if user.email:
        db_user = crud.get_user_by_email(db, user.email)
        if db_user:
            raise HTTPException(status_code=400, detail="邮箱已注册")
    
    if user.phone:
        db_user = crud.get_user_by_phone(db, user.phone)
        if db_user:
            raise HTTPException(status_code=400, detail="手机号已注册")
    
    # 密码加密（示例，实际应用请用更安全的hash）
    if not user.password:
        raise HTTPException(status_code=400, detail="密码不能为空")
    hashed_password = user.password + "notreallyhashed"
    
    return crud.create_user(db, user, hashed_password)

@router.get("/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    获取用户信息
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user
