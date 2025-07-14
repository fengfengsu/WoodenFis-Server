from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse
import hashlib
import logging
from typing import Optional
import os
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wechat", tags=["wechat"])

# 微信服务器验证配置
WECHAT_TOKEN = os.getenv("WECHAT_TOKEN", "gvtIVpdAtCQUub")

class WeChatServerVerification:
    """微信服务器验证类"""
    
    def __init__(self, token: str):
        self.token = token
    
    def verify_signature(self, signature: str, timestamp: str, nonce: str) -> bool:
        """
        验证微信服务器签名
        
        Args:
            signature: 微信加密签名
            timestamp: 时间戳
            nonce: 随机数
            
        Returns:
            bool: 验证是否成功
        """
        try:
            # 将token、timestamp、nonce三个参数进行字典序排序
            tmp_list = [self.token, timestamp, nonce]
            tmp_list.sort()
            
            # 将三个参数字符串拼接成一个字符串进行sha1加密
            tmp_str = ''.join(tmp_list)
            hash_obj = hashlib.sha1(tmp_str.encode('utf-8'))
            hash_str = hash_obj.hexdigest()
            
            # 开发者获得加密后的字符串可与signature对比，标识该请求来源于微信
            return hash_str == signature
            
        except Exception as e:
            logger.error(f"微信签名验证失败: {str(e)}")
            return False
    
    def generate_signature(self, timestamp: str, nonce: str) -> str:
        """
        生成微信签名（用于测试）
        
        Args:
            timestamp: 时间戳
            nonce: 随机数
            
        Returns:
            str: 生成的签名
        """
        tmp_list = [self.token, timestamp, nonce]
        tmp_list.sort()
        tmp_str = ''.join(tmp_list)
        hash_obj = hashlib.sha1(tmp_str.encode('utf-8'))
        return hash_obj.hexdigest()

# 创建微信验证实例
wechat_verifier = WeChatServerVerification(WECHAT_TOKEN)

@router.get("/verify", response_class=PlainTextResponse)
async def wechat_server_verify(request: Request):
    """
    微信服务器验证接口
    
    微信服务器会发送GET请求到此接口进行验证
    验证成功后需要原样返回echostr参数
    """
    try:
        # 获取微信服务器发送的参数
        signature = request.query_params.get('signature', '')
        timestamp = request.query_params.get('timestamp', '')
        nonce = request.query_params.get('nonce', '')
        echostr = request.query_params.get('echostr', '')
        
        logger.info(f"收到微信验证请求 - signature: {signature}, timestamp: {timestamp}, nonce: {nonce}")
        
        # 验证参数是否完整
        if not all([signature, timestamp, nonce, echostr]):
            logger.error("微信验证参数不完整")
            raise HTTPException(status_code=400, detail="参数不完整")
        
        # 验证签名
        if wechat_verifier.verify_signature(signature, timestamp, nonce):
            logger.info("微信服务器验证成功")
            return echostr
        else:
            logger.error("微信服务器验证失败")
            raise HTTPException(status_code=403, detail="验证失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"微信服务器验证异常: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@router.post("/webhook")
async def wechat_webhook(request: Request):
    """
    微信消息接收接口
    
    接收微信服务器推送的消息和事件
    """
    try:
        # 获取验证参数
        signature = request.query_params.get('signature', '')
        timestamp = request.query_params.get('timestamp', '')
        nonce = request.query_params.get('nonce', '')
        
        # 验证签名
        if not wechat_verifier.verify_signature(signature, timestamp, nonce):
            logger.error("微信消息推送验证失败")
            raise HTTPException(status_code=403, detail="验证失败")
        
        # 获取消息内容
        body = await request.body()
        message_content = body.decode('utf-8')
        
        logger.info(f"收到微信消息: {message_content}")
        
        # 这里可以添加消息处理逻辑
        # 例如：解析XML消息，处理不同类型的消息和事件
        
        # 返回success表示消息处理成功
        return PlainTextResponse("success")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"微信消息处理异常: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@router.get("/config")
async def get_wechat_config():
    """
    获取微信配置信息（用于调试）
    """
    return {
        "token_configured": bool(WECHAT_TOKEN and WECHAT_TOKEN != "your_wechat_token_here"),
        "verification_url": "/wechat/verify",
        "webhook_url": "/wechat/webhook",
        "timestamp": datetime.now().isoformat()
    }

@router.post("/test-signature")
async def test_signature_generation(test_data: dict):
    """
    测试签名生成（用于开发调试）
    
    Args:
        test_data: 包含timestamp和nonce的测试数据
    """
    timestamp = test_data.get('timestamp', '')
    nonce = test_data.get('nonce', '')
    
    if not timestamp or not nonce:
        raise HTTPException(status_code=400, detail="timestamp和nonce参数必填")
    
    signature = wechat_verifier.generate_signature(timestamp, nonce)
    
    return {
        "timestamp": timestamp,
        "nonce": nonce,
        "token": WECHAT_TOKEN,
        "signature": signature,
        "verification_url": f"/wechat/verify?signature={signature}&timestamp={timestamp}&nonce={nonce}&echostr=test"
    }

@router.get("/health")
async def health_check():
    """
    健康检查接口
    """
    return {
        "status": "healthy",
        "service": "wechat_verification",
        "timestamp": datetime.now().isoformat()
    }