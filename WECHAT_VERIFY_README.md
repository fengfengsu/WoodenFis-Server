# 微信服务器验证功能说明

## 概述

本项目新增了微信服务器验证功能，用于与微信公众号或小程序进行服务器端验证和消息接收。

## 文件说明

- `api/wechat_verify.py`: 微信服务器验证的主要实现文件
- 包含微信服务器验证、消息接收、配置管理等功能

## 主要功能

### 1. 服务器验证
- **接口**: `GET /wechat/verify`
- **功能**: 用于微信服务器验证开发者服务器
- **参数**: signature, timestamp, nonce, echostr
- **返回**: 验证成功返回echostr，失败返回错误信息

### 2. 消息接收
- **接口**: `POST /wechat/webhook`
- **功能**: 接收微信服务器推送的消息和事件
- **验证**: 同样需要验证signature
- **返回**: 处理成功返回"success"

### 3. 配置查看
- **接口**: `GET /wechat/config`
- **功能**: 查看当前微信配置状态
- **返回**: token配置状态、接口URL等信息

### 4. 签名测试
- **接口**: `POST /wechat/test-signature`
- **功能**: 用于开发调试，生成测试签名
- **参数**: timestamp, nonce
- **返回**: 生成的签名和验证URL

### 5. 健康检查
- **接口**: `GET /wechat/health`
- **功能**: 服务健康状态检查

## 配置说明

### 环境变量

需要在环境变量中设置微信Token：

```bash
export WECHAT_TOKEN="your_actual_wechat_token"
```

或者在`.env`文件中添加：

```
WECHAT_TOKEN=your_actual_wechat_token
```

### 微信公众号/小程序配置

1. 在微信公众号后台或小程序后台设置服务器配置
2. **服务器地址(URL)**: `https://your-domain.com/wechat/verify`
3. **Token**: 与环境变量`WECHAT_TOKEN`保持一致
4. **消息加解密方式**: 明文模式（可根据需要调整）

## 使用示例

### 1. 验证服务器

微信服务器会向验证接口发送GET请求：

```
GET /wechat/verify?signature=xxx&timestamp=xxx&nonce=xxx&echostr=xxx
```

### 2. 接收消息

微信服务器会向webhook接口发送POST请求：

```
POST /wechat/webhook?signature=xxx&timestamp=xxx&nonce=xxx
Content-Type: application/xml

<xml>
  <ToUserName><![CDATA[toUser]]></ToUserName>
  <FromUserName><![CDATA[fromUser]]></FromUserName>
  <CreateTime>123456789</CreateTime>
  <MsgType><![CDATA[text]]></MsgType>
  <Content><![CDATA[Hello]]></Content>
</xml>
```

### 3. 测试签名生成

```bash
curl -X POST "http://localhost:8000/wechat/test-signature" \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "1234567890",
    "nonce": "random_string"
  }'
```

## 安全注意事项

1. **Token保密**: 确保WECHAT_TOKEN不被泄露
2. **HTTPS**: 生产环境必须使用HTTPS
3. **签名验证**: 所有请求都会进行签名验证
4. **日志记录**: 重要操作都有日志记录

## 开发调试

### 本地测试

1. 启动服务器：
```bash
python main.py
```

2. 访问配置接口查看状态：
```bash
curl http://localhost:8000/wechat/config
```

3. 测试签名生成：
```bash
curl -X POST "http://localhost:8000/wechat/test-signature" \
  -H "Content-Type: application/json" \
  -d '{"timestamp": "1234567890", "nonce": "test"}'
```

### 内网穿透

由于微信服务器需要访问公网地址，本地开发时可以使用内网穿透工具：

- ngrok
- frp
- 花生壳等

## 错误处理

- **400**: 参数不完整
- **403**: 签名验证失败
- **500**: 服务器内部错误

所有错误都会记录到日志中，便于排查问题。

## 扩展功能

当前实现提供了基础的验证和消息接收功能，可以根据业务需求扩展：

1. 消息类型解析（文本、图片、语音等）
2. 事件处理（关注、取消关注等）
3. 自动回复功能
4. 用户管理
5. 消息加解密

## 相关文档

- [微信公众号开发文档](https://developers.weixin.qq.com/doc/offiaccount/Getting_Started/Overview.html)
- [微信小程序服务端文档](https://developers.weixin.qq.com/miniprogram/dev/api-backend/)