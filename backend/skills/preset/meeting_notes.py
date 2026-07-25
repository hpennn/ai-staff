"""会议纪要技能"""
import os
from ..llm_client import chat_completion

SKILL_META = {
    "id": "meeting_notes",
    "name": "会议纪要",
    "icon": "📝",
    "description": "会议内容整理为结构化纪要",
    "keywords": ["会议", "纪要", "记录", "会议记录", "summary", "待办", "action item"],
    "input_type": "file+text",
    "output_type": "text",
    "tags": ["会议", "纪要"],
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


async def execute(input_data: dict) -> dict:
    """
    输入: {"text": "会议内容/描述", "files": [文件列表]}
    输出: {"content": "结构化会议纪要"}
    """
    text = input_data.get("text", "")
    files = input_data.get("files", [])

    file_content = _read_file_content(files) if files else ""
    meeting_content = file_content if file_content else text

    if not meeting_content:
        return {"content": "📝 **会议纪要助手**\n\n请粘贴会议记录内容或上传会议记录文件。\n\n支持：\n- 粘贴会议文字记录/录音转写文本\n- 上传 .txt 格式的会议记录文件\n\n将自动整理为：参会人、议题、讨论要点、结论、待办事项。"}

    system = (
        "你是一位专业的会议纪要整理助手。请将以下会议内容整理为结构化的会议纪要。\n"
        "输出格式要求（Markdown）：\n\n"
        "## 会议纪要\n\n"
        "**会议主题：** [从内容中提取]\n"
        "**参会人员：** [从内容中提取，如无法提取则标注'未明确']\n"
        "**会议时间：** [从内容中提取，如无法提取则标注'未明确']\n\n"
        "### 议题与讨论要点\n"
        "- [议题1]：[讨论要点摘要]\n"
        "- [议题2]：[讨论要点摘要]\n\n"
        "### 决议事项\n"
        "1. [决议1]\n"
        "2. [决议2]\n\n"
        "### 待办事项\n"
        "| 序号 | 事项 | 负责人 | 截止时间 |\n"
        "|------|------|--------|----------|\n"
        "| 1    |      |        |          |\n\n"
        "### 备注\n"
        "[其他需要记录的信息]"
    )

    try:
        result = await chat_completion(
            [{"role": "system", "content": system},
             {"role": "user", "content": f"请整理以下会议内容为结构化纪要：\n\n{meeting_content}"}],
            max_tokens=4000
        )
        if result.startswith("[LLM未配置]"):
            return {"error": result}
        return {"content": f"📝 **会议纪要**\n\n{result}"}
    except Exception as e:
        return {"error": f"会议纪要生成失败：{str(e)}"}
