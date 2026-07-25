"""翻译助手技能"""
import os
from ..llm_client import chat_completion

SKILL_META = {
    "id": "translator",
    "name": "翻译",
    "icon": "🌐",
    "description": "多语言互译、文档翻译",
    "keywords": ["翻译", "translate", "多语言", "中英", "日文", "韩文", "法文", "德文", "西班牙"],
    "input_type": "file+text",
    "output_type": "text",
    "tags": ["翻译", "多语言"],
}

LANG_MAP = {
    "中文": "Chinese", "英语": "English", "日语": "Japanese", "韩语": "Korean",
    "法语": "French", "德语": "German", "西班牙语": "Spanish",
    "俄语": "Russian", "葡萄牙语": "Portuguese", "意大利语": "Italian",
    "阿拉伯语": "Arabic", "泰语": "Thai", "越南语": "Vietnamese",
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
    输入: {"text": "要翻译的内容或目标语言指令", "files": [文件列表]}
    输出: {"content": "翻译结果"}
    """
    text = input_data.get("text", "")
    files = input_data.get("files", [])

    file_content = _read_file_content(files) if files else ""
    source_text = file_content if file_content else text

    if not source_text:
        return {"content": "🌐 **翻译助手**\n\n请输入要翻译的内容，或上传文件进行翻译。\n\n支持语言：中文、英语、日语、韩语、法语、德语、西班牙语等。"}

    # 检测目标语言
    target_lang = None
    for cn, en in LANG_MAP.items():
        if cn in text and source_text != text:
            target_lang = en
            break

    if target_lang:
        prompt = f"请将以下文本翻译为{target_lang}，保持原文的格式和语气。只输出翻译结果，不要额外解释。\n\n{source_text}"
    else:
        prompt = (
            "请检测以下文本的语言，然后翻译为对应的语言（中文→英语，非中文→中文）。"
            "保持原文的格式和语气。只输出翻译结果，不要额外解释。\n\n"
            f"{source_text}"
        )

    try:
        result = await chat_completion(
            [{"role": "system", "content": "你是专业翻译，精通多国语言互译。翻译时保持原文的语气、风格和格式。"},
             {"role": "user", "content": prompt}],
            max_tokens=4000
        )
        if result.startswith("[LLM未配置]"):
            return {"error": result}
        return {"content": f"🌐 **翻译结果**\n\n{result}"}
    except Exception as e:
        return {"error": f"翻译失败：{str(e)}"}
