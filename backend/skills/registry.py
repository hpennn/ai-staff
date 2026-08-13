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
            "translator": ["翻译", "translate", "多语言", "中英", "英文", "日文", "韩文", "翻译一下"],
            "email_writer": ["邮件", "email", "写信", "回复邮件", "商务邮件"],
            "meeting_notes": ["会议", "纪要", "会议记录", "会议总结", "meeting"],
            "ppt_outline": ["ppt", "演示", "幻灯片", "大纲", "presentation"],
            "contract_review": ["合同审查", "合同审核", "风险", "条款审查", "合同风险"],
            "data_cleaner": ["数据清洗", "去重", "空值", "异常值", "clean", "清洗数据"],
            "file_converter": ["转pdf", "转word", "转图片", "互转", "格式转换", "文件转换", "转格式", "pdf转word", "word转pdf", "图片转pdf", "pdf转图片", "转docx", "转png", "转jpg"],
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
        from skills.preset import translator_skill, email_writer, meeting_notes
        from skills.preset import ppt_outline, contract_review, data_cleaner
        from skills.preset import file_converter

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
            # === 新增6个办公技能 ===
            SkillMeta(
                id="translator",
                name="翻译",
                icon="🌐",
                description="多语言互译、文档翻译",
                input_type="file+text",
                output_type="text",
                handler=translator_skill.execute,
                tags=["翻译", "多语言", "translate", "中英", "日文", "韩文"],
            ),
            SkillMeta(
                id="email_writer",
                name="邮件助手",
                icon="📧",
                description="根据描述生成邮件正文",
                input_type="textarea",
                output_type="text",
                handler=email_writer.execute,
                tags=["邮件", "email", "写信", "商务邮件"],
            ),
            SkillMeta(
                id="meeting_notes",
                name="会议纪要",
                icon="📝",
                description="会议内容整理为结构化纪要",
                input_type="file+text",
                output_type="text",
                handler=meeting_notes.execute,
                tags=["会议", "纪要", "会议记录", "待办"],
            ),
            SkillMeta(
                id="ppt_outline",
                name="PPT大纲",
                icon="📑",
                description="生成完整PPT结构与大纲",
                input_type="textarea",
                output_type="text",
                handler=ppt_outline.execute,
                tags=["PPT", "演示", "幻灯片", "大纲", "presentation"],
            ),
            SkillMeta(
                id="contract_review",
                name="合同审查",
                icon="🛡️",
                description="合同条款提取与风险识别",
                input_type="file",
                output_type="text",
                handler=contract_review.execute,
                tags=["合同", "审查", "风险", "条款", "法律"],
            ),
            SkillMeta(
                id="data_cleaner",
                name="数据清洗",
                icon="🧪",
                description="数据去重、格式统一、异常检测",
                input_type="file",
                output_type="text",
                handler=data_cleaner.execute,
                tags=["数据清洗", "去重", "空值", "异常值", "csv"],
            ),
            # === 新增：格式转换技能 ===
            SkillMeta(
                id="file_converter",
                name="格式转换",
                icon="🔄",
                description="图片/PDF/Word文档格式互转",
                input_type="file",
                output_type="file",
                handler=file_converter.execute,
                tags=["格式转换", "PDF", "Word", "图片", "docx", "互转"],
            ),
        ]
        for skill in preset_skills:
            self.register(skill)


# 全局实例
registry = SkillRegistry()
