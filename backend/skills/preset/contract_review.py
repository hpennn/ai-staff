"""合同审查技能"""
import os
import base64
from ..llm_client import chat_completion, vision_completion

SKILL_META = {
    "id": "contract_review",
    "name": "合同审查",
    "icon": "🛡️",
    "description": "合同条款提取与风险识别",
    "keywords": ["合同", "审查", "风险", "条款", "法律", "contract", "review"],
    "input_type": "file",
    "output_type": "text",
    "tags": ["合同", "审查"],
}


def _read_file_content(files: list) -> str:
    """从文件列表读取文本内容"""
    content_parts = []
    for f in files:
        filepath = f.get("filepath", "")
        if filepath and os.path.exists(filepath):
            ext = os.path.splitext(filepath)[1].lower()
            if ext in (".txt", ".md", ".csv", ".json", ".log"):
                with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
                    content_parts.append(fh.read())
            else:
                content_parts.append(f"[文件: {os.path.basename(filepath)}]")
    return "\n".join(content_parts)


def _get_image_data_uri(f: dict) -> str | None:
    """从文件对象获取图片data URI"""
    if "data_uri" in f:
        return f["data_uri"]
    if "base64" in f:
        return f"data:{f.get('content_type', 'image/png').split(';')[0]};base64,{f['base64']}"
    return None


def _is_image_file(filepath: str) -> bool:
    """判断文件是否为图片"""
    ext = os.path.splitext(filepath)[1].lower()
    return ext in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")


async def execute(input_data: dict) -> dict:
    """
    输入: {"text": "补充说明", "files": [文件列表]}
    输出: {"content": "合同审查结果"}
    """
    text = input_data.get("text", "")
    files = input_data.get("files", [])

    if not files:
        return {"content": "🛡️ **合同审查助手**\n\n请上传合同文档进行审查。\n\n支持：\n- 文本类：.txt / .md 等格式\n- 图片类：合同扫描件照片\n\n审查内容：\n1. 合同概要（甲乙方、标的、金额）\n2. 关键条款提取\n3. 风险点标注\n4. 修改建议"}

    system = (
        "你是一位专业的合同审查助手，具备法律知识。请对以下合同内容进行审查分析。\n"
        "请输出以下四个部分：\n\n"
        "## 一、合同概要\n"
        "- **合同类型：** [如买卖合同/服务合同/劳动合同等]\n"
        "- **甲方：** [名称]\n"
        "- **乙方：** [名称]\n"
        "- **合同标的：** [内容]\n"
        "- **合同金额：** [金额]\n"
        "- **合同期限：** [期限]\n\n"
        "## 二、关键条款提取\n"
        "| 条款 | 内容摘要 | 备注 |\n"
        "|------|----------|------|\n"
        "| 付款条款 | ... | ... |\n"
        "| 违约责任 | ... | ... |\n"
        "| 保密条款 | ... | ... |\n"
        "| 争议解决 | ... | ... |\n\n"
        "## 三、风险点标注\n"
        "1. 🔴 **高风险：** [描述]\n"
        "2. 🟡 **中风险：** [描述]\n"
        "3. 🟢 **低风险/建议：** [描述]\n\n"
        "## 四、修改建议\n"
        "1. [具体修改建议1]\n"
        "2. [具体修改建议2]\n\n"
        "**免责声明：** 本分析仅供参考，不构成法律意见。建议重大合同咨询专业律师。"
    )

    extra_note = f"\n\n用户补充说明：{text}" if text else ""

    try:
        # 检查是否有图片文件
        for f in files:
            filepath = f.get("filepath", "")
            if filepath and _is_image_file(filepath):
                # 读取图片做vision分析
                data_uri = _get_image_data_uri(f)
                if data_uri:
                    prompt = f"请审查这份合同图片的内容。{extra_note}"
                    result = await vision_completion(data_uri, prompt)
                    if result.startswith("[LLM未配置]"):
                        return {"error": result}
                    return {"content": f"🛡️ **合同审查结果**\n\n{result}"}

        # 文本类文件
        contract_text = _read_file_content(files)
        if not contract_text or contract_text.startswith("[文件:"):
            return {"error": "无法读取合同文件内容，请上传文本格式或合同扫描件图片"}

        user = f"请审查以下合同内容：\n\n{contract_text}{extra_note}"
        result = await chat_completion(
            [{"role": "system", "content": system},
             {"role": "user", "content": user}],
            max_tokens=4000
        )
        if result.startswith("[LLM未配置]"):
            return {"error": result}
        return {"content": f"🛡️ **合同审查结果**\n\n{result}"}
    except Exception as e:
        return {"error": f"合同审查失败：{str(e)}"}
