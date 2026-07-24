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
    """
    输入: {"text": "产品描述", "platform": "xiaohongshu", "angle": "种草"}
    输出: {"content": "文案内容", "titles": ["标题1", "标题2", "标题3"], "tags": ["标签"]}
    
    兼容前端：从 input_data["text"] 读取 product
    """
    # 兼容前端：text 字段作为 product
    product = input_data.get("product", "") or input_data.get("text", "")
    platform = input_data.get("platform", "xiaohongshu")
    angle = input_data.get("angle", "种草")
    if not product:
        return {"message": "文案生成就绪，请描述产品或文案需求", "content": "请描述您要生成文案的产品或内容需求。\n\n例如：\n- 一款美白面膜\n- 咖啡店新店开业\n- Python在线课程"}
    style = STYLES.get(platform, STYLES["xiaohongshu"])
    system = f"你是内容营销专家。生成{style}文案。禁止包含域名链接。"
    user = f"产品：{product}\n角度：{angle}\n输出JSON：titles(3个标题含emoji),content,tags(5个)"
    try:
        result = await chat_completion(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format={"type": "json_object"}
        )
        if result.startswith("[LLM未配置]"):
            return {"error": result}
        data = json.loads(result)
        content_text = data.get("content", result)
        titles = data.get("titles", [])
        tags = data.get("tags", [])
        # 生成格式化输出
        formatted = f"✍️ **文案生成结果**\n\n"
        if titles:
            formatted += "**标题选项：**\n"
            for i, t in enumerate(titles, 1):
                formatted += f"{i}. {t}\n"
            formatted += "\n"
        formatted += f"**正文：**\n\n{content_text}\n\n"
        if tags:
            formatted += f"**标签：** {' '.join('#' + t for t in tags)}"
        return {"content": formatted, "titles": titles, "tags": tags, "raw_content": content_text}
    except json.JSONDecodeError:
        return {"content": result, "raw_content": result}
    except Exception as e:
        return {"error": str(e)}
