from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from api import user, stat, meditation, achievement, leaderboard, share

# 初始化数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="WoodenFis Python Server", description="木鱼App后端API服务", version="1.0.0")

# 允许所有来源跨域（开发环境）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(user.router)
app.include_router(stat.router)
app.include_router(meditation.router)
app.include_router(achievement.router)
app.include_router(leaderboard.router)
app.include_router(share.router)

@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "message": "木鱼App后端API服务",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 