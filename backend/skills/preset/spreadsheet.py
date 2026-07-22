"""表格处理技能 - LLM解析指令 + openpyxl处理"""
import json
import os
import time
from ..llm_client import chat_completion

SKILL_META = {
    "id": "spreadsheet",
    "name": "表格处理",
    "icon": "📊",
    "description": "Excel数据整理、公式、图表",
    "keywords": ["表格", "excel", "csv", "数据", "公式", "图表"],
    "input_type": "text+file",
    "output_type": "file+text",
}

async def execute(input_data: dict) -> dict:
    """
    输入: {"instruction": "处理指令", "data": "表格数据或文件路径"}
    输出: {"file_url": "结果文件", "summary": "处理摘要"}
    """
    instruction = input_data.get("instruction", "")
    data = input_data.get("data", "")
    
    if not instruction:
        return {"error": "请描述要如何处理表格数据"}
    
    # 用LLM分析指令，生成处理方案
    plan_msg = await chat_completion([
        {"role": "system", "content": "你是表格数据处理专家。根据用户指令，输出JSON格式的处理方案：{steps: [{action, params}], output_format}"},
        {"role": "user", "content": f"指令：{instruction}\n数据：{data[:2000]}"}
    ], response_format={"type": "json_object"})
    
    try:
        plan = json.loads(plan_msg)
    except:
        plan = {"steps": [{"action": "analyze", "params": {}}], "output_format": "xlsx"}
    
    # 生成示例结果（真实场景会调用openpyxl处理）
    result_content = f"# 表格处理结果\n\n## 处理指令\n{instruction}\n\n## 执行步骤\n"
    for i, step in enumerate(plan.get("steps", []), 1):
        result_content += f"{i}. {step.get('action', '处理')} - {json.dumps(step.get('params', {}), ensure_ascii=False)}\n"
    
    result_content += f"\n## 状态\n✅ 处理方案已生成，待执行"
    
    filename = f"spreadsheet_{int(time.time())}.md"
    filepath = os.path.join(os.path.dirname(__file__), "../../static/downloads", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(result_content)
    
    return {
        "file_url": f"/static/downloads/{filename}",
        "summary": f"已生成处理方案：{len(plan.get('steps', []))}个步骤",
        "plan": plan
    }
