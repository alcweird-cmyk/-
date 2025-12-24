from fastapi import FastAPI, Request, HTTPException, Query, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
import json
import glob
from datetime import datetime
import logging
from pathlib import Path
import uvicorn
from PIL import Image
import io
import base64
import time
from functools import lru_cache
import shutil
import requests

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="遥感推理服务监控系统", version="1.0.0")

# 静态文件目录
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板目录
templates_dir = Path("templates")
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory="templates")

# 项目路径配置 - 修复路径配置
PROJECT_ROOT = Path.cwd()  # 使用当前工作目录
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"  # 修改为当前目录下的logs
DETECTED_IMAGES_DIR = DATA_DIR / "detected_result_images"
DETECTED_JSON_DIR = DATA_DIR / "detected_result_json_files"

# 缓存配置
CACHE_DURATION = 60  # 缓存60秒，减少API调用频率
cache_data = {}
cache_timestamps = {}

def get_cached_data(key):
    """获取缓存数据"""
    if key in cache_data and key in cache_timestamps:
        if time.time() - cache_timestamps[key] < CACHE_DURATION:
            return cache_data[key]
    return None

def set_cached_data(key, data):
    """设置缓存数据"""
    cache_data[key] = data
    cache_timestamps[key] = time.time()

def clear_cache():
    """清除所有缓存"""
    cache_data.clear()
    cache_timestamps.clear()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页 - 显示实时监控仪表板"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    """历史记录页面"""
    return templates.TemplateResponse("history.html", {"request": request})

@app.get("/results", response_class=HTMLResponse)
async def results(request: Request):
    """检测结果页面"""
    return templates.TemplateResponse("results.html", {"request": request})

@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """上传检测页面"""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/test-layout", response_class=HTMLResponse)
async def test_layout(request: Request):
    """布局测试页面"""
    return FileResponse("test_layout.html")

@app.get("/api/tasks/current")
async def get_current_task():
    """获取当前任务状态"""
    try:
        # 检查缓存
        cached_task = get_cached_data('current_task')
        if cached_task:
            return cached_task
        
        # 检查是否有正在运行的任务
        log_files = list(LOGS_DIR.glob("*.log")) if LOGS_DIR.exists() else []
        
        if log_files:
            # 获取最新的日志文件
            latest_log = max(log_files, key=os.path.getctime)
            with open(latest_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    if "定时任务开始" in last_line:
                        result = {
                            "status": "running",
                            "message": "推理任务正在运行中",
                            "last_update": datetime.now().isoformat(),
                            "log_file": str(latest_log)
                        }
                        set_cached_data('current_task', result)
                        return result
        
        result = {
            "status": "idle",
            "message": "当前无运行中的任务",
            "last_update": datetime.now().isoformat()
        }
        set_cached_data('current_task', result)
        return result
    except Exception as e:
        logger.error(f"获取当前任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/history")
async def get_task_history():
    """获取历史任务记录"""
    try:
        # 检查缓存
        cached_history = get_cached_data('task_history')
        if cached_history:
            return cached_history
        
        tasks = []
        
        # 从JSON结果文件中获取历史记录
        if DETECTED_JSON_DIR.exists():
            json_files = list(DETECTED_JSON_DIR.glob("*.json"))
            for json_file in sorted(json_files, key=os.path.getctime, reverse=True):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 从文件名提取时间戳
                    filename = json_file.stem
                    if "detect_result_" in filename:
                        timestamp_str = filename.replace("detect_result_", "")
                        try:
                            task_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                        except:
                            task_time = datetime.fromtimestamp(os.path.getctime(json_file))
                    else:
                        task_time = datetime.fromtimestamp(os.path.getctime(json_file))
                    
                    # 查找对应的图片文件
                    image_files = []
                    if DETECTED_IMAGES_DIR.exists():
                        # 查找同时间戳的图片文件
                        for img_ext in ["*.png", "*.jpg", "*.jpeg", "*.tif"]:
                            pattern = f"*{timestamp_str}*{img_ext[1:]}"
                            image_files.extend([str(f) for f in DETECTED_IMAGES_DIR.glob(pattern)])
                    
                    task_info = {
                        "id": filename,
                        "timestamp": task_time.isoformat(),
                        "status": "completed",
                        "result_path": str(json_file),
                        "image_files": image_files,
                        "summary": {
                            "异常区域": data.get("异常区域检测", {}),
                            "水利设施": data.get("重点水利设施检测", {}),
                            "地物分类": data.get("地物分类", {}),
                            "水体提取": data.get("水体自动提取", {})
                        }
                    }
                    tasks.append(task_info)
                except Exception as e:
                    logger.warning(f"解析任务文件 {json_file} 失败: {e}")
                    continue
        
        result = {"tasks": tasks}
        set_cached_data('task_history', result)
        return result
    except Exception as e:
        logger.error(f"获取历史任务记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/{task_id}")
async def get_task_detail(task_id: str):
    """获取特定任务的详细信息"""
    try:
        json_file = DETECTED_JSON_DIR / f"{task_id}.json"
        if not json_file.exists():
            raise HTTPException(status_code=404, detail="任务不存在")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            "id": task_id,
            "data": data,
            "result_path": str(json_file)
        }
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs")
async def get_system_logs(limit: int = 100, force: int = Query(0, description="强制刷新缓存")):
    """获取系统运行日志"""
    try:
        cache_key = f'logs_{limit}'
        if force:
            set_cached_data(cache_key, None)  # 清除缓存
        cached_logs = get_cached_data(cache_key)
        if cached_logs:
            return cached_logs
        logs = []
        if LOGS_DIR.exists():
            log_files = list(LOGS_DIR.glob("*.log"))
            if log_files:
                latest_log = max(log_files, key=os.path.getctime)
                logger.info(f"读取日志文件: {latest_log}")
                try:
                    with open(latest_log, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for line in lines[-limit:]:
                            logs.append(line.strip())
                except UnicodeDecodeError:
                    with open(latest_log, 'r', encoding='gbk') as f:
                        lines = f.readlines()
                        for line in lines[-limit:]:
                            logs.append(line.strip())
        else:
            logger.warning(f"日志目录不存在: {LOGS_DIR}")
        result = {"logs": logs}
        set_cached_data(cache_key, result)
        return result
    except Exception as e:
        logger.error(f"获取系统日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_system_stats():
    """获取系统统计信息"""
    try:
        # 检查缓存
        cached_stats = get_cached_data('system_stats')
        if cached_stats:
            return cached_stats
        
        stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "total_images": 0,
            "last_task_time": None,
            "system_status": "unknown"
        }
        
        # 统计任务数量
        if DETECTED_JSON_DIR.exists():
            json_files = list(DETECTED_JSON_DIR.glob("*.json"))
            stats["total_tasks"] = len(json_files)
            stats["completed_tasks"] = len(json_files)
            
            if json_files:
                latest_file = max(json_files, key=os.path.getctime)
                stats["last_task_time"] = datetime.fromtimestamp(os.path.getctime(latest_file)).isoformat()
        
        # 统计图片数量
        if DETECTED_IMAGES_DIR.exists():
            image_files = []
            for ext in ["*.png", "*.jpg", "*.jpeg", "*.tif"]:
                image_files.extend(list(DETECTED_IMAGES_DIR.glob(ext)))
            stats["total_images"] = len(image_files)
        
        # 检查系统状态
        current_task = await get_current_task()
        stats["system_status"] = current_task["status"]
        
        # 缓存结果
        set_cached_data('system_stats', stats)
        
        return stats
    except Exception as e:
        logger.error(f"获取系统统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/images")
async def get_detected_images():
    """获取检测结果图片列表"""
    try:
        images = []
        if DETECTED_IMAGES_DIR.exists():
            for ext in ["*.png", "*.jpg", "*.jpeg", "*.tif"]:
                for img_file in DETECTED_IMAGES_DIR.glob(ext):
                    try:
                        # 获取文件信息
                        stat = img_file.stat()
                        file_size = stat.st_size
                        file_size_mb = file_size / (1024 * 1024)
                        
                        images.append({
                            "filename": img_file.name,
                            "path": str(img_file),
                            "size_mb": round(file_size_mb, 2),
                            "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
                    except Exception as e:
                        logger.warning(f"获取图片信息失败 {img_file}: {e}")
                        continue
        
        # 按修改时间排序，最新的在前
        images.sort(key=lambda x: x["modified_time"], reverse=True)
        return {"images": images}
    except Exception as e:
        logger.error(f"获取检测结果图片失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/images/{filename}/thumbnail")
async def get_image_thumbnail(filename: str):
    """获取图片缩略图"""
    try:
        image_path = DETECTED_IMAGES_DIR / filename
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="图片不存在")
        
        # 创建缩略图
        with Image.open(image_path) as img:
            # 计算缩略图尺寸，保持宽高比
            max_size = (400, 300)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 转换为base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return {"thumbnail": f"data:image/png;base64,{img_str}"}
    except Exception as e:
        logger.error(f"生成缩略图失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/images/{filename}/download")
async def download_image(filename: str):
    """下载原始图片"""
    try:
        image_path = DETECTED_IMAGES_DIR / filename
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="图片不存在")
        
        return FileResponse(
            path=image_path,
            filename=filename,
            media_type='application/octet-stream'
        )
    except Exception as e:
        logger.error(f"下载图片失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/json-files")
async def get_json_files():
    """获取JSON结果文件列表"""
    try:
        json_files = []
        if DETECTED_JSON_DIR.exists():
            for json_file in DETECTED_JSON_DIR.glob("*.json"):
                try:
                    stat = json_file.stat()
                    file_size = stat.st_size
                    file_size_kb = file_size / 1024
                    
                    json_files.append({
                        "filename": json_file.name,
                        "path": str(json_file),
                        "size_kb": round(file_size_kb, 2),
                        "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except Exception as e:
                    logger.warning(f"获取JSON文件信息失败 {json_file}: {e}")
                    continue
        
        # 按修改时间排序，最新的在前
        json_files.sort(key=lambda x: x["modified_time"], reverse=True)
        return {"json_files": json_files}
    except Exception as e:
        logger.error(f"获取JSON文件列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/json-files/{filename}/content")
async def get_json_content(filename: str):
    """获取JSON文件内容"""
    try:
        json_path = DETECTED_JSON_DIR / filename
        if not json_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {"content": data}
    except Exception as e:
        logger.error(f"读取JSON文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clear-cache")
async def clear_cache_endpoint():
    """清除所有缓存"""
    try:
        clear_cache()
        return {"message": "缓存已清除", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"清除缓存失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload-and-detect")
async def upload_and_detect(
    image: UploadFile = File(...),
    categories: str = Form(...),
    is_change_detection: bool = Form(True),
    is_only_change_detection: bool = Form(False),
    legend_required: bool = Form(False)
):
    """上传图片并进行检测"""
    try:
        # 创建上传目录
        upload_dir = DATA_DIR / "uploaded_images"
        upload_dir.mkdir(exist_ok=True)
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_filename = image.filename or "unknown"
        file_extension = Path(original_filename).suffix
        unique_filename = f"upload_{timestamp}{file_extension}"
        image_path = upload_dir / unique_filename
        
        # 保存上传的图片
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        # 解析类别
        categories_list = json.loads(categories)
        
        # 准备调用推理API的数据
        detect_data = {
            "image_to_be_detected_address": str(image_path),
            "categories": categories_list,
            "is_change_detection": is_change_detection,
            "is_only_change_detection": is_only_change_detection,
            "legend_required": legend_required
        }
        
        logger.info(f"开始检测图片: {unique_filename}")
        logger.info(f"检测参数: {detect_data}")
        
        # 调用推理API
        try:
            response = requests.put(
                "http://127.0.0.1:8085/detect/with_data_base_plate",
                json=detect_data,
                timeout=300  # 5分钟超时
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"检测成功: {result}")
                # 先尝试从推理API返回的json里提取图片名
                result_image_filename = ""
                if isinstance(result, dict):
                    result_image_path = result.get("最终检测结果路径", "")
                    if not result_image_path and 'data' in result and isinstance(result['data'], dict):
                        result_image_path = result['data'].get("最终检测结果路径", "")
                    if not result_image_path:
                        for key in result.keys():
                            if "检测结果路径" in key and isinstance(result[key], str):
                                result_image_path = result[key]
                                break
                    if result_image_path:
                        result_image_filename = os.path.basename(result_image_path)
                # 兜底：无论如何都要返回本地最新的图片
                if not result_image_filename or not (DETECTED_IMAGES_DIR / result_image_filename).exists():
                    image_files = sorted(DETECTED_IMAGES_DIR.glob('*.png'), key=os.path.getctime, reverse=True)
                    if image_files:
                        result_image_filename = image_files[0].name
                return {
                    "status": "success",
                    "message": "检测完成",
                    "timestamp": datetime.now().isoformat(),
                    "result_json": result,
                    "result_images": [result_image_filename] if result_image_filename else [],
                    "uploaded_file": unique_filename
                }
            else:
                logger.error(f"推理API返回错误: {response.status_code} - {response.text}")
                raise HTTPException(status_code=500, detail=f"推理服务错误: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"调用推理API失败: {e}")
            raise HTTPException(status_code=500, detail=f"推理服务连接失败: {str(e)}")
            
    except Exception as e:
        logger.error(f"上传检测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 从环境变量获取端口，默认为8086
    import os
    port = int(os.environ.get("MONITOR_PORT", 8086))
    
    # 优化启动配置
    uvicorn.run(
        "monitor_web:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True,
        reload_dirs=["templates", "static"],  # 只监控模板和静态文件
        reload_excludes=["*.pyc", "*.log", "data/*", "logs/*", "test/*"],  # 排除不需要监控的文件
        workers=1,  # 单进程避免缓存冲突
        access_log=True,
        log_level="info"
    ) 