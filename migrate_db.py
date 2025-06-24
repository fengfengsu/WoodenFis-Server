"""
数据库迁移脚本

为支持手机号验证码登录功能，需要：
1. 在users表中添加phone字段
2. 创建verification_codes表
3. 将email和hashed_password字段改为可空
"""

from sqlalchemy import create_engine, text
from database import SQLALCHEMY_DATABASE_URL, engine
import models
from models import Base

def migrate_database():
    """执行数据库迁移"""
    print("🔄 开始数据库迁移...")
    
    try:
        # 创建所有表（如果不存在）
        Base.metadata.create_all(bind=engine)
        print("✅ 创建新表结构完成")
        
        # 检查users表是否有phone字段
        with engine.connect() as conn:
            # 查询表结构
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result]
            
            if 'phone' not in columns:
                print("📱 添加phone字段到users表...")
                conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR"))
                conn.execute(text("CREATE UNIQUE INDEX idx_users_phone ON users (phone)"))
                conn.commit()
                print("✅ phone字段添加完成")
            else:
                print("✅ phone字段已存在")
            
            # 检查verification_codes表是否存在
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='verification_codes'"))
            if not result.fetchone():
                print("📝 创建verification_codes表...")
                conn.execute(text("""
                    CREATE TABLE verification_codes (
                        id INTEGER PRIMARY KEY,
                        phone VARCHAR,
                        code VARCHAR,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        expires_at DATETIME,
                        used BOOLEAN DEFAULT 0
                    )
                """))
                conn.execute(text("CREATE INDEX idx_verification_codes_phone ON verification_codes (phone)"))
                conn.commit()
                print("✅ verification_codes表创建完成")
            else:
                print("✅ verification_codes表已存在")
        
        print("🎉 数据库迁移完成！")
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        raise e

def test_migration():
    """测试迁移后的数据库"""
    print("\n🧪 测试迁移后的数据库...")
    
    try:
        with engine.connect() as conn:
            # 测试users表结构
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result]
            required_columns = ['id', 'username', 'email', 'phone', 'hashed_password', 'avatar', 'is_vip', 'vip_expire_date', 'merit_points', 'created_at']
            
            for col in required_columns:
                if col in columns:
                    print(f"✅ users.{col} 字段存在")
                else:
                    print(f"❌ users.{col} 字段缺失")
            
            # 测试verification_codes表结构
            result = conn.execute(text("PRAGMA table_info(verification_codes)"))
            columns = [row[1] for row in result]
            required_columns = ['id', 'phone', 'code', 'created_at', 'expires_at', 'used']
            
            for col in required_columns:
                if col in columns:
                    print(f"✅ verification_codes.{col} 字段存在")
                else:
                    print(f"❌ verification_codes.{col} 字段缺失")
        
        print("✅ 数据库结构测试通过")
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")

if __name__ == "__main__":
    migrate_database()
    test_migration() 