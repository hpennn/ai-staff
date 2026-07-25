"""数据清洗技能"""
import os
import csv
from ..llm_client import chat_completion

SKILL_META = {
    "id": "data_cleaner",
    "name": "数据清洗",
    "icon": "🧪",
    "description": "数据去重、格式统一、异常检测",
    "keywords": ["数据清洗", "去重", "空值", "异常值", "clean", "data cleaning", "csv"],
    "input_type": "file",
    "output_type": "text",
    "tags": ["数据", "清洗"],
}


def _read_csv_preview(filepath: str, max_rows: int = 15) -> dict:
    """读取CSV文件并返回预览信息"""
    result = {
        "filepath": filepath,
        "filename": os.path.basename(filepath),
        "total_rows": 0,
        "columns": [],
        "preview": "",
        "error": None,
    }
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            # 尝试检测分隔符
            sample = f.read(2048)
            f.seek(0)
            sniffer = csv.Sniffer()
            try:
                dialect = sniffer.sniff(sample)
                delimiter = dialect.delimiter
            except csv.Error:
                delimiter = ","

            reader = csv.reader(f, delimiter=delimiter)
            rows = list(reader)

            if not rows:
                result["error"] = "文件为空"
                return result

            result["columns"] = rows[0] if rows else []
            result["total_rows"] = len(rows) - 1  # 减去表头

            # 生成预览
            preview_rows = rows[:max_rows + 1]  # 包含表头
            preview_lines = []
            for i, row in enumerate(preview_rows):
                preview_lines.append(" | ".join(str(cell)[:30] for cell in row))
            result["preview"] = "\n".join(preview_lines)

    except Exception as e:
        result["error"] = str(e)
    return result


def _read_excel_preview(filepath: str, max_rows: int = 15) -> dict:
    """尝试读取Excel文件"""
    result = {
        "filepath": filepath,
        "filename": os.path.basename(filepath),
        "total_rows": 0,
        "columns": [],
        "preview": "",
        "error": None,
    }
    try:
        import openpyxl
        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        ws = wb.active
        rows = []
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i > max_rows:
                break
            rows.append([str(cell) if cell is not None else "" for cell in row])
        wb.close()

        if not rows:
            result["error"] = "文件为空"
            return result

        result["columns"] = rows[0] if rows else []
        result["total_rows"] = max(0, len(rows) - 1)
        preview_lines = [" | ".join(cell[:30] for cell in row) for row in rows]
        result["preview"] = "\n".join(preview_lines)
    except ImportError:
        result["error"] = "需要安装 openpyxl 库来读取 Excel 文件"
    except Exception as e:
        result["error"] = str(e)
    return result


async def execute(input_data: dict) -> dict:
    """
    输入: {"text": "清洗需求描述", "files": [文件列表]}
    输出: {"content": "数据清洗分析报告"}
    """
    text = input_data.get("text", "")
    files = input_data.get("files", [])

    if not files:
        return {"content": "🧪 **数据清洗助手**\n\n请上传 CSV 或 Excel 文件进行数据清洗分析。\n\n分析内容：\n1. 数据概况（行列数、字段类型）\n2. 缺失值检测\n3. 重复行检测\n4. 异常值识别\n5. 清洗建议与示例代码"}

    # 读取文件内容
    preview_data = None
    for f in files:
        filepath = f.get("filepath", "")
        if not filepath or not os.path.exists(filepath):
            continue
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".csv":
            preview_data = _read_csv_preview(filepath)
            break
        elif ext in (".xlsx", ".xls"):
            preview_data = _read_excel_preview(filepath)
            break

    if not preview_data:
        return {"error": "未找到可处理的 CSV/Excel 文件，请上传 .csv 或 .xlsx 文件"}

    if preview_data.get("error"):
        return {"error": f"文件读取失败：{preview_data['error']}"}

    # 构造分析prompt
    user_msg = (
        f"请分析以下数据文件并进行清洗建议：\n\n"
        f"文件名：{preview_data['filename']}\n"
        f"总行数：{preview_data['total_rows']}\n"
        f"列名：{', '.join(preview_data['columns'])}\n\n"
        f"数据预览（前15行）：\n{preview_data['preview']}\n\n"
    )
    if text:
        user_msg += f"\n用户特别需求：{text}\n"

    user_msg += (
        "\n请输出以下内容：\n"
        "## 一、数据概况\n"
        "- 行列数、字段名称与推测类型\n\n"
        "## 二、数据质量问题\n"
        "1. **缺失值**：[哪些列有缺失，预估比例]\n"
        "2. **重复行**：[是否有重复，预估数量]\n"
        "3. **异常值**：[可能的异常值]\n"
        "4. **格式不一致**：[日期格式、编码等]\n\n"
        "## 三、清洗建议\n"
        "[具体的清洗步骤建议]\n\n"
        "## 四、Python 示例代码\n"
        "```python\n"
        "import pandas as pd\n"
        "# 提供可直接运行的清洗代码\n"
        "```"
    )

    try:
        result = await chat_completion(
            [{"role": "system", "content": "你是数据分析与清洗专家，擅长用pandas处理数据问题。"},
             {"role": "user", "content": user_msg}],
            max_tokens=4000
        )
        if result.startswith("[LLM未配置]"):
            return {"error": result}

        summary = (
            f"📊 **数据概况**\n"
            f"- 文件：{preview_data['filename']}\n"
            f"- 行数：{preview_data['total_rows']}\n"
            f"- 列数：{len(preview_data['columns'])}\n"
            f"- 字段：{', '.join(preview_data['columns'][:10])}"
        )
        return {"content": f"{summary}\n\n{result}"}
    except Exception as e:
        return {"error": f"数据分析失败：{str(e)}"}
