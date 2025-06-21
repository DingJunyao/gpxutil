from datetime import datetime

from fastapi import APIRouter, HTTPException, Path

from src.gpxutil_server.core.db import REDIS_CLIENT

router = APIRouter(prefix="/task", tags=["task"])

@router.get("/{task_id}/progress", name="获取任务进度", description="获取任务进度")
async def get_task_progress(task_id: str = Path(title="任务 ID", description='要查询的任务 ID')):
    # 从Redis获取进度数据
    progress_data = REDIS_CLIENT.hgetall(f"task_progress:{task_id}")

    if not progress_data:
        raise HTTPException(status_code=404, detail="Task not found")

    # 解析数据
    total = int(progress_data[b'total'])
    error = int(progress_data[b'error'])
    completed = int(progress_data[b'completed'])
    start_time = datetime.fromisoformat(progress_data[b'start_time'].decode())
    last_update = datetime.fromisoformat(progress_data[b'last_update'].decode())
    executed = completed + error

    # 计算进度百分比
    percent = (executed / total) * 100 if total > 0 else 0

    # 计算时间
    elapsed = (last_update - start_time).total_seconds()

    # 估算剩余时间（基于平均速度）
    remaining = (elapsed / executed) * (total - executed) if executed > 0 else 0

    return {
        "task_id": task_id,
        "progress": {
            "percent": round(percent, 1),
            "completed": completed,
            "error": error,
            "total": total
        },
        "timing": {
            "elapsed_seconds": round(elapsed, 1),
            "estimated_remaining_seconds": round(remaining, 1)
        },
        "last_updated": last_update.isoformat()
    }