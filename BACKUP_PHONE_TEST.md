# 第三方登录备份手机号功能测试指南

## 功能概述

为了增强用户账户的安全性和可恢复性，我们为木鱼应用的第三方登录功能添加了备份手机号机制。

### 新增功能

1. **用户表扩展**：
   - `backup_phone`: 备份手机号
   - `login_type`: 登录类型（phone, apple, wechat）
   - `is_phone_verified`: 手机号是否已验证
   - `phone`: 改为可空字段，支持第三方登录用户

2. **新增API接口**：
   - `POST /users/bind-backup-phone`: 为第三方登录用户绑定备份手机号
   - `POST /users/update-backup-phone`: 更新用户备份手机号
   - `GET /users/users-by-login-type/{login_type}`: 根据登录类型获取用户列表

## 数据库迁移

### 迁移结果
- ✅ 数据库迁移已完成
- ✅ 现有用户数据已保留
- ✅ 现有用户登录类型已设置为 "phone"
- ✅ 现有用户手机号验证状态已设置为已验证

### 迁移统计
- 迁移后用户总数: 2
- 登录类型分布: phone: 2

## API测试

### 1. 测试Apple登录（带备份机制）

```bash
# Apple登录
curl -X POST "http://localhost:8000/users/apple-login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "Apple用户",
    "email": "apple@example.com",
    "platform": "apple",
    "platform_user_id": "apple_123456",
    "auth_code": "test_apple_token",
    "icon": "https://example.com/avatar.jpg"
  }'
```

### 2. 测试微信登录（带备份机制）

```bash
# 微信登录
curl -X POST "http://localhost:8000/users/wechat-login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "微信用户",
    "email": "wechat@example.com",
    "platform": "wechat",
    "platform_user_id": "wechat_123456",
    "auth_code": "test_wechat_code",
    "icon": "https://example.com/wechat_avatar.jpg"
  }'
```

### 3. 为第三方登录用户绑定备份手机号

```bash
# 绑定备份手机号（假设用户ID为3）
curl -X POST "http://localhost:8000/users/bind-backup-phone" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 3,
    "phone": "+8613800138000"
  }'
```

### 4. 更新备份手机号

```bash
# 更新备份手机号
curl -X POST "http://localhost:8000/users/update-backup-phone" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 3,
    "backup_phone": "+8613900139000"
  }'
```

### 5. 根据登录类型查询用户

```bash
# 查询Apple登录用户
curl "http://localhost:8000/users/users-by-login-type/apple"

# 查询微信登录用户
curl "http://localhost:8000/users/users-by-login-type/wechat"

# 查询手机号登录用户
curl "http://localhost:8000/users/users-by-login-type/phone"
```

## 业务逻辑说明

### 1. 第三方登录用户创建
- 新用户通过Apple/微信登录时，`login_type`自动设置为对应平台
- `phone`字段为空，`is_phone_verified`为false
- 可以后续绑定手机号作为备份

### 2. 备份手机号绑定
- 第三方登录用户可以绑定手机号作为账户恢复方式
- 绑定时会验证手机号并设置`is_phone_verified`为true
- 如果用户已有手机号，原手机号会移动到`backup_phone`字段

### 3. 登录类型管理
- `phone`: 传统手机号+验证码登录
- `apple`: Apple Sign In登录
- `wechat`: 微信授权登录

## 安全考虑

1. **账户恢复**：第三方登录用户绑定手机号后，可以通过手机号找回账户
2. **多重验证**：支持多种登录方式，提高账户安全性
3. **数据备份**：重要的联系方式信息有备份机制

## 测试场景

### 场景1：新用户Apple登录
1. 用户首次使用Apple登录
2. 系统创建新用户，`login_type`为"apple"
3. 用户可选择绑定手机号作为备份

### 场景2：新用户微信登录
1. 用户首次使用微信登录
2. 系统创建新用户，`login_type`为"wechat"
3. 用户可选择绑定手机号作为备份

### 场景3：第三方用户绑定手机号
1. 第三方登录用户绑定手机号
2. 系统验证手机号并设置为已验证
3. 用户现在可以通过手机号或第三方平台登录

### 场景4：管理员查询用户
1. 管理员可以按登录类型查询用户
2. 便于用户管理和数据分析

## 注意事项

1. **数据库备份**：迁移前已自动创建数据库备份
2. **向后兼容**：现有手机号登录功能不受影响
3. **API兼容性**：新增API不影响现有接口
4. **错误处理**：所有新接口都有适当的错误处理和验证

## 下一步开发

1. **iOS客户端适配**：更新iOS客户端以支持备份手机号绑定
2. **账户恢复流程**：实现通过备份手机号恢复第三方登录账户
3. **用户设置界面**：添加备份手机号管理功能
4. **安全验证**：增强手机号验证流程