#!/usr/bin/env python3
"""
数据库迁移脚本：为User表添加第三方登录备份字段

新增字段：
- backup_phone: 备份手机号
- login_type: 登录类型（phone, apple, wechat）
- is_phone_verified: 手机号是否已验证

同时将现有phone字段改为可空
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """执行数据库迁移"""
    db_path = "woodenfis.db"
    
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在，跳过迁移")
        return
    
    # 备份数据库
    backup_path = f"wooden_fish_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"数据库已备份到: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查是否已经存在新字段
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'backup_phone' in columns:
            print("迁移已完成，跳过")
            return
        
        print("开始数据库迁移...")
        
        # 1. 创建新的users表结构
        cursor.execute("""
        CREATE TABLE users_new (
            id INTEGER PRIMARY KEY,
            username VARCHAR UNIQUE,
            email VARCHAR UNIQUE,
            phone VARCHAR UNIQUE,
            hashed_password VARCHAR,
            avatar VARCHAR,
            is_vip BOOLEAN DEFAULT 0,
            vip_expire_date DATETIME,
            merit_points INTEGER DEFAULT 0,
            backup_phone VARCHAR,
            login_type VARCHAR DEFAULT 'phone',
            is_phone_verified BOOLEAN DEFAULT 0,
            created_at DATETIME
        )
        """)
        
        # 2. 复制现有数据到新表
        cursor.execute("""
        INSERT INTO users_new (
            id, username, email, phone, hashed_password, avatar, 
            is_vip, vip_expire_date, merit_points, created_at,
            login_type, is_phone_verified
        )
        SELECT 
            id, username, email, phone, hashed_password, avatar,
            is_vip, vip_expire_date, merit_points, created_at,
            CASE 
                WHEN phone IS NOT NULL THEN 'phone'
                ELSE 'phone'
            END as login_type,
            CASE 
                WHEN phone IS NOT NULL THEN 1
                ELSE 0
            END as is_phone_verified
        FROM users
        """)
        
        # 3. 删除旧表
        cursor.execute("DROP TABLE users")
        
        # 4. 重命名新表
        cursor.execute("ALTER TABLE users_new RENAME TO users")
        
        # 5. 重新创建索引
        cursor.execute("CREATE UNIQUE INDEX ix_users_username ON users (username)")
        cursor.execute("CREATE UNIQUE INDEX ix_users_email ON users (email)")
        cursor.execute("CREATE UNIQUE INDEX ix_users_phone ON users (phone)")
        cursor.execute("CREATE INDEX ix_users_backup_phone ON users (backup_phone)")
        cursor.execute("CREATE INDEX ix_users_id ON users (id)")
        
        # 6. 更新现有第三方登录用户的登录类型
        cursor.execute("""
        UPDATE users 
        SET login_type = (
            SELECT CASE 
                WHEN tpa.platform = 'apple' THEN 'apple'
                WHEN tpa.platform = 'wechat' THEN 'wechat'
                ELSE 'phone'
            END
            FROM third_party_auth tpa
            WHERE tpa.user_id = users.id
            LIMIT 1
        )
        WHERE id IN (
            SELECT DISTINCT user_id FROM third_party_auth
        )
        """)
        
        conn.commit()
        print("数据库迁移完成！")
        
        # 验证迁移结果
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"迁移后用户总数: {user_count}")
        
        cursor.execute("SELECT login_type, COUNT(*) FROM users GROUP BY login_type")
        login_types = cursor.fetchall()
        print("登录类型分布:")
        for login_type, count in login_types:
            print(f"  {login_type}: {count}")
            
    except Exception as e:
        conn.rollback()
        print(f"迁移失败: {e}")
        # 恢复备份
        conn.close()
        shutil.copy2(backup_path, db_path)
        print(f"已从备份恢复数据库")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()