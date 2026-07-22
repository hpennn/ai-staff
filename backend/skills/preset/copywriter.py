"""文案生成技能"""
import json
from ..llm_client import chat_completion

SKILL_META = {
    "id": "copywriter",
    "name": "文案生成",
    "icon": "✍️",
    "description": "营销文案、小红书、公众号",
    "keywords": ["文案", "营销", "小红书", "公众号", "短视频"],
    "input_type": "text",
    "output_type": "text",
}

STYLES = {
    "xiaohongshu": "小红书风格：口语化带emoji，像用户分享，200-400字",
    "wechat": "公众号风格：专业有温度，800-1500字",
    "douyin": "短视频脚本：15-30秒，有hook，节奏快",
    "zhihu": "知乎回答：专业详细有数据，500-1000字",
}

async def execute(input_data: dict) -> dict:
    product = input_data.get("product", "")
    platform = input_data.get("platform", "xiaohongshu")
    angle = input_data.get("angle", "种草")
    if not product:
        return {"message": "文案生成就绪，请描述产品"}
    style = STYLES.get(platform, STYLES["xiaohongshu"])
    system = f"你是内容营销专家。生成{style}文案。禁止包含域名链接。"
    user = f"产品：{product}\n角度：{angle}\n输出JSON：titles(3个标题含emoji),content,tags(5个)"
    try:
        result = await chat_completion(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format={"type": "json_object"}
        )
        data = json.loads(result)
        return {"content": data.get("content", result), "titles": data.get("titles", []), "tags": data.get("tags", [])}
    except Exception as e:
        return {"error": str(e)}
