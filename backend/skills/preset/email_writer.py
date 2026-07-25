"""邮件助手技能"""
from ..llm_client import chat_completion

SKILL_META = {
    "id": "email_writer",
    "name": "邮件助手",
    "icon": "📧",
    "description": "根据描述生成邮件正文",
    "keywords": ["邮件", "email", "写信", "回复", "正式邮件", "商务邮件"],
    "input_type": "textarea",
    "output_type": "text",
    "tags": ["邮件", "写作"],
}

TONE_PROMPTS = {
    "正式": "使用正式、专业的商务语气",
    "简洁": "使用简洁明了的语气，言简意赅",
    "热情": "使用热情友好的语气",
    "委婉": "使用委婉、礼貌的语气",
    "紧急": "使用紧迫但礼貌的语气，强调时效性",
}


def _detect_tone(text: str) -> str:
    """从用户文本中检测语气"""
    for tone, _ in TONE_PROMPTS.items():
        if tone in text:
            return tone
    return "正式"


async def execute(input_data: dict) -> dict:
    """
    输入: {"text": "描述邮件需求"}
    输出: {"content": "邮件正文"}
    """
    text = input_data.get("text", "")
    if not text:
        return {"content": "📧 **邮件助手**\n\n请描述你要生成的邮件内容需求。\n\n示例：\n- 给客户的报价邮件\n- 向领导请假\n- 回复合作伙伴的合作邀请\n- 项目进度汇报邮件\n\n支持语气：正式、简洁、热情、委婉、紧急"}

    tone = _detect_tone(text)
    tone_desc = TONE_PROMPTS.get(tone, TONE_PROMPTS["正式"])

    system = (
        "你是一位专业的邮件撰写助手。请根据用户需求生成完整的邮件正文。\n"
        "要求：\n"
        "1. 包含适当的称呼（如：尊敬的XX、XX您好）\n"
        "2. 正文结构清晰、逻辑通顺\n"
        "3. 包含恰当的结束语（如：此致敬礼、期待您的回复）\n"
        "4. 根据内容判断是否需要签名栏\n"
        "5. 直接输出邮件内容，不要额外解释"
    )
    user = f"请帮我撰写一封邮件：\n{text}\n\n语气要求：{tone_desc}。请直接输出完整邮件内容。"

    try:
        result = await chat_completion(
            [{"role": "system", "content": system},
             {"role": "user", "content": user}],
            max_tokens=2000
        )
        if result.startswith("[LLM未配置]"):
            return {"error": result}
        return {"content": f"📧 **邮件内容**\n\n{result}"}
    except Exception as e:
        return {"error": f"邮件生成失败：{str(e)}"}
