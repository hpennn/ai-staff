"""
Skill Registry - 技能注册中心
负责注册、发现、加载技能
"""
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class SkillMeta:
    """技能元数据"""
    id: str
    name: str
    icon: str
    description: str
    input_type: str  # "textarea", "file", "file+text"
    output_type: str  # "text", "file", "structured"
    handler: Optional[Callable] = None
    tags: List[str] = field(default_factory=list)
    enabled: bool = True


class SkillRegistry:
    """技能注册中心 - 单例模式"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._skills = {}
            cls._instance._initialized = False
        return cls._instance

    def register(self, skill: SkillMeta) -> None:
        """注册一个技能"""
        self._skills[skill.id] = skill

    def unregister(self, skill_id: str) -> None:
        """注销一个技能"""
        self._skills.pop(skill_id, None)

    def get(self, skill_id: str) -> Optional[SkillMeta]:
        """获取技能元数据"""
        return self._skills.get(skill_id)

    def list_all(self, enabled_only: bool = True) -> List[SkillMeta]:
        """列出所有技能"""
        skills = list(self._skills.values())
        if enabled_only:
            skills = [s for s in skills if s.enabled]
        return skills

    def find_by_keyword(self, keyword: str) -> List[SkillMeta]:
        """根据关键词匹配技能"""
        keyword_lower = keyword.lower()
        matched = []
        for skill in self._skills.values():
            if not skill.enabled:
                continue
            if (keyword_lower in skill.name.lower() or
                keyword_lower in skill.description.lower() or
                any(keyword_lower in tag.lower() for tag in skill.tags)):
                matched.append(skill)
        return matched

    def find_by_keywords(self, text: str) -> Optional[SkillMeta]:
        """从文本中匹配最合适的技能"""
        keyword_map = {
            "doc_generator": ["文档", "报告", "合同", "word", "pdf", "markdown", "写作", "公文"],
            "spreadsheet": ["表格", "excel", "数据整理", "公式", "图表", "xlsx", "csv"],
            "image_processor": ["图片", "水印", "裁剪", "格式转换", "批量处理", "resize", "压缩"],
            "ocr": ["识别", "文字", "ocr", "图片转文字", "票据", "扫描件", "读图"],
            "data_extractor": ["提取", "数据提取", "表格数据", "结构化", "解析", "抽取"],
            "copywriter": ["文案", "营销", "小红书", "公众号", "推广", "种草", "标题", "内容"],
        }
        text_lower = text.lower()
        for skill_id, keywords in keyword_map.items():
            if any(kw in text_lower for kw in keywords):
                skill = self.get(skill_id)
                if skill and skill.enabled:
                    return skill
        return None

    def load_preset_skills(self) -> None:
        """加载所有预置技能"""
        from skills.preset import doc_generator, spreadsheet, image_processor
        from skills.preset import ocr_skill, data_extractor, copywriter

        preset_skills = [
            SkillMeta(
                id="doc_generator",
                name="文档生成",
                icon="📄",
                description="Word/PDF/Markdown自动生成",
                input_type="textarea",
                output_type="file",
                handler=doc_generator.execute,
                tags=["文档", "word", "pdf", "markdown", "报告", "合同"],
            ),
            SkillMeta(
                id="spreadsheet",
                name="表格处理",
                icon="📊",
                description="Excel数据整理、公式、图表",
                input_type="file+text",
                output_type="file",
                handler=spreadsheet.execute,
                tags=["表格", "excel", "数据", "公式", "图表", "xlsx"],
            ),
            SkillMeta(
                id="image_processor",
                name="图片处理",
                icon="🖼️",
                description="图片→文字、票据识别",
                input_type="file",
                output_type="file",
                handler=image_processor.execute,
                tags=["图片", "水印", "裁剪", "格式转换", "压缩"],
            ),
            SkillMeta(
                id="ocr",
                name="OCR识别",
                icon="🔍",
                description="图片→文字、票据识别",
                input_type="file",
                output_type="text",
                handler=ocr_skill.execute,
                tags=["识别", "OCR", "文字", "票据", "扫描件"],
            ),
            SkillMeta(
                id="data_extractor",
                name="数据提取",
                icon="📈",
                description="图片/文本→结构化数据提取",
                input_type="file",
                output_type="structured",
                handler=data_extractor.execute,
                tags=["提取", "数据", "表格", "结构化", "解析"],
            ),
            SkillMeta(
                id="copywriter",
                name="文案生成",
                icon="✍️",
                description="营销文案、公众号、小红书内容",
                input_type="textarea",
                output_type="text",
                handler=copywriter.execute,
                tags=["文案", "营销", "小红书", "公众号", "推广", "种草"],
            ),
        ]

        for skill in preset_skills:
            self.register(skill)


# 全局实例
registry = SkillRegistry()
