from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.common.config import API_HOST, API_PORT, init_directories
from src.common.logger import setup_logger

# ロガーの設定
logger = setup_logger("api")

# アプリケーションの初期化
app = FastAPI(
    title="Knowledge Acquisition System API",
    description="情報収集・知識管理サブシステム API",
    version="0.1.0",
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 起動時の初期化
@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    logger.info("Starting Knowledge Acquisition System API")
    init_directories()
    logger.info("Initialization completed")

# ルートエンドポイント
@app.get("/")
async def root():
    """APIルートエンドポイント"""
    logger.debug("Root endpoint accessed")
    return {"message": "Welcome to Knowledge Acquisition System API"}

# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    logger.debug("Health check accessed")
    return {"status": "healthy"}

# アプリケーションの実行
if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting uvicorn server on {API_HOST}:{API_PORT}")
    uvicorn.run(app, host=API_HOST, port=API_PORT)