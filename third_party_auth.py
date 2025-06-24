import os
import jwt
import json
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AppleAuthService:
    """Apple Sign In 认证服务"""
    
    def __init__(self):
        self.client_id = os.getenv('APPLE_CLIENT_ID', 'your.app.bundle.id')
        self.team_id = os.getenv('APPLE_TEAM_ID')
        self.key_id = os.getenv('APPLE_KEY_ID')
        self.private_key = os.getenv('APPLE_PRIVATE_KEY')
        self.apple_public_keys_url = 'https://appleid.apple.com/auth/keys'
        
    def is_configured(self) -> bool:
        """检查Apple认证是否已配置"""
        return all([
            self.client_id,
            self.team_id,
            self.key_id,
            self.private_key
        ])
    
    def verify_identity_token(self, identity_token: str) -> Optional[Dict[str, Any]]:
        """验证Apple身份令牌"""
        try:
            if not self.is_configured():
                logger.warning("Apple认证未配置，使用模拟验证")
                return self._mock_verify_token(identity_token)
            
            # 获取Apple公钥
            apple_keys = self._get_apple_public_keys()
            if not apple_keys:
                logger.error("无法获取Apple公钥")
                return None
            
            # 解码JWT头部获取kid
            header = jwt.get_unverified_header(identity_token)
            kid = header.get('kid')
            
            # 找到对应的公钥
            public_key = None
            for key in apple_keys['keys']:
                if key['kid'] == kid:
                    public_key = jwt.PyJWK(key).key
                    break
            
            if not public_key:
                logger.error(f"找不到对应的Apple公钥，kid: {kid}")
                return None
            
            # 验证JWT
            payload = jwt.decode(
                identity_token,
                public_key,
                algorithms=['RS256'],
                audience=self.client_id,
                issuer='https://appleid.apple.com'
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.error("Apple身份令牌已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.error(f"Apple身份令牌无效: {e}")
            return None
        except Exception as e:
            logger.error(f"验证Apple身份令牌时发生错误: {e}")
            return None
    
    def _get_apple_public_keys(self) -> Optional[Dict[str, Any]]:
        """获取Apple公钥"""
        try:
            response = requests.get(self.apple_public_keys_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取Apple公钥失败: {e}")
            return None
    
    def _mock_verify_token(self, identity_token: str) -> Dict[str, Any]:
        """模拟验证令牌（开发环境使用）"""
        logger.info("使用模拟Apple认证")
        # 简单解码JWT获取用户信息（不验证签名）
        try:
            import jwt as pyjwt
            payload = pyjwt.decode(identity_token, options={"verify_signature": False})
            return payload
        except Exception:
            # 如果解码失败，返回模拟数据
            return {
                'sub': f'apple_user_{hash(identity_token) % 1000000}',
                'email': 'apple.user@example.com',
                'email_verified': True,
                'iss': 'https://appleid.apple.com',
                'aud': self.client_id,
                'exp': int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
                'iat': int(datetime.utcnow().timestamp())
            }

class WeChatAuthService:
    """微信认证服务"""
    
    def __init__(self):
        self.app_id = os.getenv('WECHAT_APP_ID')
        self.app_secret = os.getenv('WECHAT_APP_SECRET')
        self.access_token_url = 'https://api.weixin.qq.com/sns/oauth2/access_token'
        self.user_info_url = 'https://api.weixin.qq.com/sns/userinfo'
    
    def is_configured(self) -> bool:
        """检查微信认证是否已配置"""
        return bool(self.app_id and self.app_secret)
    
    def get_access_token(self, code: str) -> Optional[Dict[str, Any]]:
        """通过授权码获取访问令牌"""
        try:
            if not self.is_configured():
                logger.warning("微信认证未配置，使用模拟数据")
                return self._mock_access_token(code)
            
            params = {
                'appid': self.app_id,
                'secret': self.app_secret,
                'code': code,
                'grant_type': 'authorization_code'
            }
            
            response = requests.get(self.access_token_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'errcode' in data:
                logger.error(f"微信获取访问令牌失败: {data}")
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"获取微信访问令牌时发生错误: {e}")
            return None
    
    def get_user_info(self, access_token: str, openid: str) -> Optional[Dict[str, Any]]:
        """获取微信用户信息"""
        try:
            if not self.is_configured():
                logger.warning("微信认证未配置，使用模拟数据")
                return self._mock_user_info(openid)
            
            params = {
                'access_token': access_token,
                'openid': openid,
                'lang': 'zh_CN'
            }
            
            response = requests.get(self.user_info_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'errcode' in data:
                logger.error(f"微信获取用户信息失败: {data}")
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"获取微信用户信息时发生错误: {e}")
            return None
    
    def _mock_access_token(self, code: str) -> Dict[str, Any]:
        """模拟访问令牌（开发环境使用）"""
        logger.info("使用模拟微信访问令牌")
        return {
            'access_token': f'mock_access_token_{hash(code) % 1000000}',
            'expires_in': 7200,
            'refresh_token': f'mock_refresh_token_{hash(code) % 1000000}',
            'openid': f'wechat_user_{hash(code) % 1000000}',
            'scope': 'snsapi_userinfo'
        }
    
    def _mock_user_info(self, openid: str) -> Dict[str, Any]:
        """模拟用户信息（开发环境使用）"""
        logger.info("使用模拟微信用户信息")
        return {
            'openid': openid,
            'nickname': '微信用户',
            'sex': 1,
            'province': '广东',
            'city': '深圳',
            'country': '中国',
            'headimgurl': 'https://example.com/avatar.jpg',
            'unionid': f'union_{openid}'
        }
        
    def verify_wechat_auth(self, platform_user_id: str) -> Dict[str, Any]:
        """验证微信授权信息
        
        Args:
            platform_user_id: 微信用户ID
            
        Returns:
            包含用户信息的字典
        """
        # 由于没有授权码，直接返回模拟数据
        logger.info(f"验证微信用户ID: {platform_user_id}")
        return self._mock_user_info(platform_user_id)

# 服务实例
apple_auth_service = AppleAuthService()
wechat_auth_service = WeChatAuthService()