import os
from typing import Optional
from alibabacloud_dysmsapi20170525.client import Client as DysmsapiClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_models
from alibabacloud_tea_util import models as util_models
import json
import logging

logger = logging.getLogger(__name__)

class SMSService:
    """阿里云短信服务封装类"""
    
    def __init__(self):
        # 从环境变量获取配置，如未设置则使用默认值
        self.access_key_id = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID', 'LTAI5t7JTDD1HXPyK8E7WbRN')
        self.access_key_secret = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET', 'ASkZsiBk4ikXrSbxaSH4CdsJ8LNrFs')
        self.sign_name = os.getenv('SMS_SIGN_NAME', '木鱼APP')  # 短信签名
        self.template_code = os.getenv('SMS_TEMPLATE_CODE', 'SMS_123456789')  # 短信模板代码
        self.endpoint = 'dysmsapi.aliyuncs.com'
        
        # 检查密钥是否有效（非空字符串）
        if not self.access_key_id or not self.access_key_secret or len(self.access_key_id.strip()) == 0 or len(self.access_key_secret.strip()) == 0:
            logger.warning("阿里云短信服务配置不完整，将使用模拟模式")
            self.client = None
        else:
            logger.info("使用阿里云短信服务")
            self.client = self._create_client()
    
    def _create_client(self) -> Optional[DysmsapiClient]:
        """创建阿里云短信客户端"""
        try:
            config = open_api_models.Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret
            )
            config.endpoint = self.endpoint
            return DysmsapiClient(config)
        except Exception as e:
            logger.error(f"创建阿里云短信客户端失败: {e}")
            logger.debug(f"使用的配置: access_key_id={self.access_key_id[:4]}***, endpoint={self.endpoint}")
            return None
    
    def send_verification_code(self, phone: str, code: str) -> dict:
        """发送验证码短信
        
        Args:
            phone: 手机号
            code: 验证码
            
        Returns:
            dict: 发送结果
        """
        if not self.client:
            # 模拟模式，用于开发测试
            logger.info(f"模拟发送短信到 {phone}，验证码: {code}")
            return {
                'success': True,
                'message': f'验证码已发送到 {phone}（模拟模式）',
                'code': 'OK',
                'request_id': 'mock_request_id'
            }
        
        try:
            # 构建短信发送请求
            send_sms_request = dysmsapi_models.SendSmsRequest(
                phone_numbers=phone,
                sign_name=self.sign_name,
                template_code=self.template_code,
                template_param=json.dumps({'code': code})  # 模板参数
            )
            
            runtime = util_models.RuntimeOptions()
            
            # 发送短信
            response = self.client.send_sms_with_options(send_sms_request, runtime)
            
            # 解析响应
            if response.status_code == 200:
                body = response.body
                if body.code == 'OK':
                    logger.info(f"短信发送成功: {phone}, RequestId: {body.request_id}")
                    return {
                        'success': True,
                        'message': f'验证码已发送到 {phone}',
                        'code': body.code,
                        'request_id': body.request_id
                    }
                else:
                    logger.error(f"短信发送失败: {body.code} - {body.message}")
                    return {
                        'success': False,
                        'message': f'短信发送失败: {body.message}',
                        'code': body.code,
                        'request_id': body.request_id
                    }
            else:
                logger.error(f"短信发送请求失败: HTTP {response.status_code}")
                return {
                    'success': False,
                    'message': '短信发送请求失败',
                    'code': 'HTTP_ERROR',
                    'request_id': None
                }
                
        except Exception as e:
            logger.error(f"发送短信异常: {e}")
            return {
                'success': False,
                'message': f'短信发送异常: {str(e)}',
                'code': 'EXCEPTION',
                'request_id': None
            }
    
    def is_configured(self) -> bool:
        """检查短信服务是否已正确配置"""
        return self.client is not None
        
    def update_credentials(self, access_key_id: str, access_key_secret: str) -> bool:
        """更新阿里云访问凭证
        
        Args:
            access_key_id: 阿里云访问密钥ID
            access_key_secret: 阿里云访问密钥密钥
            
        Returns:
            bool: 更新是否成功
        """
        if not access_key_id or not access_key_secret:
            logger.error("无法更新凭证：提供的密钥为空")
            return False
            
        try:
            # 更新实例变量
            self.access_key_id = access_key_id
            self.access_key_secret = access_key_secret
            
            # 重新创建客户端
            self.client = self._create_client()
            
            if self.client:
                logger.info("阿里云短信服务凭证已成功更新")
                return True
            else:
                logger.error("阿里云短信服务凭证更新后，客户端创建失败")
                return False
                
        except Exception as e:
            logger.error(f"更新阿里云短信服务凭证时发生错误: {e}")
            return False

# 全局短信服务实例
sms_service = SMSService()