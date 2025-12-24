from fastapi import FastAPI, Request
from utils.config_loader import load_config
from utils.model_loader import load_models
from routers import detection_router    
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from utils.log_config import setup_logging

setup_logging()  # 日志初始化，必须在其它import之前
import logging
logger = logging.getLogger(__name__)

class IPAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed_ips):
        super().__init__(app)
        self.allowed_ips = allowed_ips

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        if client_ip not in self.allowed_ips:
            return JSONResponse(
                status_code=403,
                content={"detail": f"IP {client_ip} not allowed."}
            )
        return await call_next(request)

app = FastAPI()

# 先加载一次config用于中间件
config = load_config()
allowed_ips = config.get("allowed_ips", [])
app.add_middleware(IPAuthMiddleware, allowed_ips=allowed_ips)

# Load configuration and models on startup
@app.on_event("startup")
async def startup_event():  
    app.state.config = config
    app.state.models = await load_models(app.state.config)

# Include routers for different functionalities
app.include_router(detection_router.router, prefix="/detect", tags=["Detection"])

if __name__ == "__main__":
    uvicorn.run("main:app",host="0.0.0.0", port=8085, reload=True)