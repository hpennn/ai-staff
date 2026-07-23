"""
Skills API Router - 技能API路由，含积分检查
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List
from pydantic import BaseModel

from skills.registry import registry
from skills.engine import engine
from credits_database import register_user, get_user_credits, deduct_credits

router = APIRouter()

# 技能执行消耗积分
CREDIT_COST_SKILL = 20


class ExecuteRequest(BaseModel):
    """技能执行请求"""
    text: Optional[str] = ""
    format: Optional[str] = None
    platform: Optional[str] = None
    style: Optional[str] = None
    extra: Optional[dict] = None
    user_id: Optional[str] = ""  # 设备ID，用于积分检查


class TaskCreateRequest(BaseModel):
    """任务创建请求"""
    input: str
    skill_id: Optional[str] = None
    user_id: Optional[str] = ""  # 设备ID，用于积分检查


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
    """执行指定技能，含积分检查"""
    # ===== 积分检查 =====
    remaining_credits = -1
    if request.user_id:
        register_user(request.user_id)
        credits = get_user_credits(request.user_id)
        if credits < CREDIT_COST_SKILL:
            raise HTTPException(
                status_code=402,
                detail={
                    "message": "积分不足，请充值后继续使用",
                    "required": CREDIT_COST_SKILL,
                    "remaining": credits,
                }
            )

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

    # ===== 技能执行成功后扣积分 =====
    if request.user_id:
        deduct_credits(request.user_id, CREDIT_COST_SKILL, f"技能执行: {skill_id}")
        remaining_credits = get_user_credits(request.user_id)

    result_dict = result.to_dict()
    result_dict["remaining_credits"] = remaining_credits
    return result_dict


@router.post("/tasks")
async def create_task(request: TaskCreateRequest):
    """创建任务（自动匹配技能），含积分检查"""
    # ===== 积分检查 =====
    remaining_credits = -1
    if request.user_id:
        register_user(request.user_id)
        credits = get_user_credits(request.user_id)
        if credits < CREDIT_COST_SKILL:
            raise HTTPException(
                status_code=402,
                detail={
                    "message": "积分不足，请充值后继续使用",
                    "required": CREDIT_COST_SKILL,
                    "remaining": credits,
                }
            )

    if request.skill_id:
        result = await engine.execute(
            request.skill_id, {"text": request.input}
        )
    else:
        result = await engine.auto_execute(request.input)

    # ===== 任务执行成功后扣积分 =====
    if request.user_id:
        skill_desc = request.skill_id or "自动匹配"
        deduct_credits(request.user_id, CREDIT_COST_SKILL, f"任务执行: {skill_desc}")
        remaining_credits = get_user_credits(request.user_id)

    result_dict = result.to_dict()
    result_dict["remaining_credits"] = remaining_credits
    return result_dict


@router.get("/tasks")
async def get_tasks(limit: int = 50):
    """获取任务历史"""
    tasks = engine.get_task_history(limit)
    return {"tasks": tasks, "total": len(tasks)}
