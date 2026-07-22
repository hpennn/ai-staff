"""
Skills API Router - 技能API路由
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List
from pydantic import BaseModel

from skills.registry import registry
from skills.engine import engine

router = APIRouter()


class ExecuteRequest(BaseModel):
    """技能执行请求"""
    text: Optional[str] = ""
    format: Optional[str] = None
    platform: Optional[str] = None
    style: Optional[str] = None
    extra: Optional[dict] = None


class TaskCreateRequest(BaseModel):
    """任务创建请求"""
    input: str
    skill_id: Optional[str] = None


@router.get("/skills")
async def list_skills():
    """获取所有可用技能列表"""
    skills = registry.list_all()
    return {
        "skills": [
            {
                "id": s.id,
                "name": s.name,
                "icon": s.icon,
                "description": s.description,
                "input_type": s.input_type,
                "output_type": s.output_type,
                "tags": s.tags,
                "enabled": s.enabled,
            }
            for s in skills
        ]
    }


@router.get("/skills/{skill_id}")
async def get_skill(skill_id: str):
    """获取单个技能详情"""
    skill = registry.get(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="技能不存在")
    return {
        "id": skill.id,
        "name": skill.name,
        "icon": skill.icon,
        "description": skill.description,
        "input_type": skill.input_type,
        "output_type": skill.output_type,
        "tags": skill.tags,
        "enabled": skill.enabled,
    }


@router.post("/skills/{skill_id}/execute")
async def execute_skill(
    skill_id: str,
    request: ExecuteRequest,
    files: Optional[List[UploadFile]] = None,
):
    """执行指定技能"""
    input_data = {"text": request.text or ""}
    if request.format:
        input_data["format"] = request.format
    if request.platform:
        input_data["platform"] = request.platform
    if request.style:
        input_data["style"] = request.style
    if request.extra:
        input_data.update(request.extra)
    if files:
        input_data["files"] = [f.filename for f in files]

    result = await engine.execute(skill_id, input_data)
    return result.to_dict()


@router.post("/tasks")
async def create_task(request: TaskCreateRequest):
    """创建任务（自动匹配技能）"""
    if request.skill_id:
        result = await engine.execute(
            request.skill_id, {"text": request.input}
        )
    else:
        result = await engine.auto_execute(request.input)
    return result.to_dict()


@router.get("/tasks")
async def get_tasks(limit: int = 50):
    """获取任务历史"""
    tasks = engine.get_task_history(limit)
    return {"tasks": tasks, "total": len(tasks)}
