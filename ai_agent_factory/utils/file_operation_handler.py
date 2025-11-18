from pathlib import Path
import re
import os

import json
import os
from typing import List, Dict, Any, Optional, Set

# 假设你能调用 Grok / Claude / GPT / DeepSeek / Qwen 等
# 这里以一个统一的调用函数为例
import json
import re
from typing import List, Dict, Any
from ai_agent_factory.llms.base_llm_openai import BaseLLM

def llm_extract_file_operations(
    text: str,
    llm: BaseLLM,
    model: str = None,           # 如果不传，就用 llm 本身的 model
    temperature: float = 0.0,    # 提取任务必须确定性
    max_retries: int = 2
) -> List[Dict[str, Any]]:
    """
    【终极稳健方案】用大模型安全提取文件操作指令
    支持任意乱七八糟的输入，永远不会错
    """
    system_prompt = """
你是一个极度严谨的文件操作指令提取器。
你的任务是：从用户提供的任意文本中，精准识别出所有明确的文件操作意图，并严格按以下 JSON 格式输出数组。

支持的 6 种操作（不区分大小写）：
1. create_file → {"operation": "CREATE_FILE", "path": "xxx", "content": "任意内容，保留换行和引号"}
2. update_file  → 同上结构
3. read_file    → {"operation": "READ_FILE", "path": "xxx"}
4. delete_file  → {"operation": "DELETE_FILE", "path": "xxx"}
5. list_files   → {"operation": "LIST_FILES"}
6. again        → {"operation": "AGAIN", "reason": "用户说明的原因"}

核心规则（必须严格遵守）：
- 多个操作按出现顺序放入数组
- content 字段原样保留所有换行、引号、代码、甚至 XML 标签
- 如果完全没有操作意图，返回 []
- 如果不确定某个操作，宁可不提取，也不要乱猜
- 只输出纯 JSON 数组，禁止任何解释、markdown、```json 围栏、换行说明
- path 不允许包含 ../，但你不用校验，只原样提取
""".strip()

    user_prompt = f"请提取以下文字中的所有文件操作指令：\n\n{text.strip()}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt}
    ]

    for attempt in range(max_retries + 1):
        try:
            # 使用你现有的 OpenAILLM 实例（支持流式）
            full_response = ""
            stream = llm.chat(
                context=messages
            )
            for token in stream:
                full_response += token

            # 清理可能的 markdown 围栏（极少数模型会加）
            cleaned = full_response.strip()
            if cleaned.startswith("```"):
                # 去掉 ```json 和 ```
                cleaned = re.sub(r"^```json\s*|```$", "", cleaned, flags=re.IGNORECASE).strip()

            # 解析 JSON
            operations = json.loads(cleaned)

            if not isinstance(operations, list):
                raise ValueError("返回的不是 JSON 数组")

            # 标准化 operation 名称为大写
            for op in operations:
                if "operation" in op:
                    op["operation"] = op["operation"].upper()

            print(f"LLM 成功提取 {len(operations)} 个文件操作")
            return operations

        except json.JSONDecodeError as e:
            print(f"第 {attempt + 1} 次提取 JSON 失败: {e}\n模型输出:\n{full_response}")
            if attempt == max_retries:
                print("达到最大重试次数，降级使用正则解析")
                return parse_structured_operations(text)  # 你的原正则函数兜底
        except Exception as e:
            print(f"LLM 提取异常: {e}")
            if attempt == max_retries:
                print("降级使用正则解析")
                return parse_structured_operations(text)

    return []

def parse_structured_operations(text: str):
    """
    安全解析结构化文件操作指令
    支持：<tag attr="val">content</tag> 和 <tag attr="val" />
    """
    if not text or not isinstance(text, str):
        return []

    operations = []
    # 匹配闭合标签：<tag attrs>content</tag>
    block_pattern = r'<(\w+)\s*([^>]*)>(.*?)</\1\s*>'
    # 匹配自闭合标签：<tag attrs />
    self_closing_pattern = r'<(\w+)\s*([^>]*)/\s*>'

    # 先找闭合标签
    for match in re.finditer(block_pattern, text, re.DOTALL):
        tag_name = match.group(1).strip()
        attrs_str = match.group(2).strip()
        content = match.group(3)

        attrs = _parse_attributes(attrs_str)
        operations.append({
            "operation": tag_name.upper(),
            "attributes": attrs,
            "content": content.strip() if content else None,
            "self_closing": False
        })

    # 再找自闭合标签
    for match in re.finditer(self_closing_pattern, text, re.DOTALL):
        tag_name = match.group(1).strip()
        attrs_str = match.group(2).strip()

        attrs = _parse_attributes(attrs_str)
        operations.append({
            "operation": tag_name.upper(),
            "attributes": attrs,
            "content": None,
            "self_closing": True
        })

    return operations


def _parse_attributes(attr_str: str) -> dict:
    """解析属性字符串为字典"""
    if not attr_str:
        return {}
    attrs = {}
    # 匹配 key="value" 或 key='value'
    pattern = r'(\w+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\')'
    for key, v1, v2 in re.findall(pattern, attr_str):
        attrs[key] = v1 or v2
    return attrs


# ===========================
# 📁 文件操作处理器（重构版）
# ===========================

class FileOperationHandler:
    """文件操作指令处理器 - 支持结构化标签语法"""

    # 你可以根据项目类型继续扩展这几个集合
    IGNORED_DIRS: Set[str] = {
        # Python
        "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
        ".venv", "venv", "env", ".env",
        # Node.js
        "node_modules", ".next", "dist", "build", ".nuxt", ".output",
        # Git / IDE / OS
        ".git", ".idea", ".vscode", ".DS_Store",
        # 其他常见临时目录
        ".tmp", "tmp", "temp", ".cache", ".log"
    }

    IGNORED_PREFIXES: Set[str] = {
        # 常见临时文件前缀
        "node_", "tmp_", "temp_", ".tmp_", "cache_",
        # Python 字节码
        "__pycache__"
    }

    IGNORED_EXTENSIONS: Set[str] = {
        # 日志、缓存、二进制等无意义文件
        ".log", ".tmp", ".temp", ".cache", ".bak", ".swp", ".swo",
        ".pyc", ".pyo", ".pyd",
        ".DS_Store", ".lnk", ".exe", ".dll", ".so", ".dylib"
    }

    @staticmethod
    def get_file_operation_prompt():
        """获取支持结构化标签的提示词"""
        return (
            "📁 文件操作指令支持：\n"
            "请使用以下 XML-like 标签格式包围操作指令：\n\n"

            "<create_file path=\"相对路径\">\n"
            "文件内容（支持多行）\n"
            "</create_file>\n\n"

            "<read_file path=\"文件名\" />\n\n"

            "<update_file path=\"相对路径\">\n"
            "新内容\n"
            "</update_file>\n\n"

            "<delete_file path=\"文件名\" />\n\n"

            "<list_files />\n\n"


            "📌 规则说明：\n"
            "- 所有路径相对于 output/ 目录\n"
            "- 不允许 ../ 路径穿越\n"
            "- 内容可包含换行、冒号、引号等字符\n"
            "- 如果需要分步决策，请返回 <again reason=\"...\" />\n"
            "- 系统将自动执行并反馈结果，您可以基于新状态继续操作。\n\n"
            "- 一次最多返回3条文件操作指令,如果未完成，请加一条 <again reason=\"...\" />"

           
        )

    def __init__(self, output_dir="output",llm: BaseLLM = None):
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        self.llm = llm  # ← 新增：注入你的 LLM 实例
        self.created_files = []  # 记录成功创建的文件路径

    @staticmethod
    def has_file_operations(text: str) -> bool:
        """
        快速判断输入文本是否包含任何文件操作标签
        :param text: 输入字符串
        :return: 是否包含操作指令
        """
        if not text or not isinstance(text, str):
            return False

        # 常见操作标签名称
        operation_tags = (
            'create_file', 'read_file', 'update_file',
            'delete_file', 'list_files', 'again'
        )

        # 构造正则：匹配 <tag ...> 或 <tag ... />
        pattern = r'<(' + '|'.join(operation_tags) + r')\s*[^>]*/?\s*(?:>|/>|>.*?</\1>)'
        return bool(re.search(pattern, text, re.IGNORECASE | re.DOTALL))
    
    def handle_tagged_file_operations(self, text: str, callback=None) -> bool:
        if not text:
            return False

        # 优先使用大模型提取（超级稳）
        if self.llm:
            operations = llm_extract_file_operations(text, self.llm)
        else:
            # 没传 LLM 就用旧正则（兼容历史）
            operations = parse_structured_operations(text)

        if not operations:
            return False

        print(f"检测并执行 {len(operations)} 个文件操作指令")
        for i, op in enumerate(operations):
            # 确保 operation 是大写（兼容各种模型输出）
            op["operation"] = op.get("operation", "").upper()
            print(f"  [{i+1}] {op['operation']} → {op.get('attributes', {}).get('path') or op.get('path', '')}")
            result = self.execute_operation(op)
            if callback:
                callback(op, result)

        return True

    def execute_operation(self, op_dict: dict):
        """执行单个结构化操作"""
        op = op_dict["operation"]
        if not op_dict.__contains__("attributes"):
            attrs =  op_dict;
        else:
            attrs = op_dict["attributes"]
        if not op == "AGAIN":
            content = op_dict["content"]
        try:
            if op == "CREATE_FILE":
                path = attrs.get("path")
                if not path:
                    return {"success": False, "error": "缺少 path 属性"}
                return self.create_file(path, content or "")

            elif op == "READ_FILE":
                path = attrs.get("path")
                if not path:
                    return {"success": False, "error": "缺少 path 属性"}
                return self.read_file(path)

            elif op == "UPDATE_FILE":
                path = attrs.get("path")
                if not path:
                    return {"success": False, "error": "缺少 path 属性"}
                return self.update_file(path, content or "")

            elif op == "DELETE_FILE":
                path = attrs.get("path")
                if not path:
                    return {"success": False, "error": "缺少 path 属性"}
                return self.delete_file(path)

            elif op == "LIST_FILES":
                return self.list_files()

            elif op == "AGAIN":
                reason = attrs.get("reason", "无明确原因")
                print(f"🔁 请求再次处理: {reason}")
                return {
                    "success": True,
                    "operation": "AGAIN",
                    "reason": reason,
                    "requires_follow_up": True
                }

            else:
                print(f"⚠️ 未知操作: {op}")
                return {"success": False, "error": f"不支持的操作: {op}", "operation": op}

        except Exception as e:
            print(f"❌ 执行 {op} 时异常: {e}")
            return {"success": False, "error": str(e), "operation": op}

    def _validate_path(self, filename: str) -> tuple[bool, str]:
        """验证路径合法性，防止路径穿越"""
        full_path = os.path.join(self.output_dir, filename)
        full_path = os.path.normpath(full_path)
        if not full_path.startswith(self.output_dir + os.sep):
            return False, f"非法路径（路径逃逸检测）: {filename}"
        return True, full_path

    def create_file(self, filename: str, content: str):
        """创建文件"""
        print(f"📁 创建文件 → {filename}")
        valid, res = self._validate_path(filename)
        if not valid:
            print(f"❌ {res}")
            return {"success": False, "error": res}
        full_path = res

        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.created_files.append(full_path)
            print(f"✅ 成功创建: {full_path}")
            return {
                "success": True,
                "operation": "CREATE_FILE",
                "filename": filename,
                "path": full_path,
                "size": len(content)
            }
        except Exception as e:
            err_msg = f"写入失败: {e}"
            print(f"❌ {err_msg}")
            return {"success": False, "error": err_msg, "filename": filename}

    def read_file(self, filename: str):
        """读取文件"""
        print(f"📖 读取文件 ← {filename}")
        valid, res = self._validate_path(filename)
        if not valid:
            print(f"❌ {res}")
            return {"success": False, "error": res}
        full_path = res

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            preview = content[:100] + ('...' if len(content) > 100 else '')
            print(f"📄 内容预览 ({len(content)} 字): {preview}")
            return {
                "success": True,
                "operation": "READ_FILE",
                "filename": filename,
                "content": content,
                "path": full_path
            }
        except FileNotFoundError:
            print(f"❌ 文件不存在: {full_path}")
            return {"success": False, "error": "文件不存在", "filename": filename}
        except Exception as e:
            err_msg = f"读取失败: {e}"
            print(f"❌ {err_msg}")
            return {"success": False, "error": err_msg, "filename": filename}

    def update_file(self, filename: str, content: str):
        """更新文件"""
        print(f"✏️ 更新文件 → {filename}")
        valid, res = self._validate_path(filename)
        if not valid:
            print(f"❌ {res}")
            return {"success": False, "error": res}
        full_path = res

        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 文件已更新: {full_path}")
            return {
                "success": True,
                "operation": "UPDATE_FILE",
                "filename": filename,
                "path": full_path,
                "size": len(content)
            }
        except Exception as e:
            err_msg = f"更新失败: {e}"
            print(f"❌ {err_msg}")
            return {"success": False, "error": err_msg, "filename": filename}

    def delete_file(self, filename: str):
        """删除文件"""
        print(f"🗑️ 删除文件 × {filename}")
        valid, res = self._validate_path(filename)
        if not valid:
            print(f"❌ {res}")
            return {"success": False, "error": res}
        full_path = res

        try:
            os.remove(full_path)
            if full_path in self.created_files:
                self.created_files.remove(full_path)
            print(f"✅ 已删除: {full_path}")
            return {
                "success": True,
                "operation": "DELETE_FILE",
                "filename": filename,
                "path": full_path
            }
        except FileNotFoundError:
            print(f"❌ 文件不存在，无需删除: {full_path}")
            return {"success": False, "error": "文件不存在", "filename": filename}
        except Exception as e:
            err_msg = f"删除失败: {e}"
            print(f"❌ {err_msg}")
            return {"success": False, "error": err_msg, "filename": filename}

    def list_files(
        self,
        include_hidden: bool = False,      # 是否显示 .开头的文件（如 .env）
        max_depth: int = None,             # 最大递归深度，None 表示无限制
        extra_ignore_dirs: Set[str] = None
    ) -> dict:
        """
        列出 output 目录下的所有文件（智能过滤垃圾文件）
        """
        print("列出项目文件（已智能过滤临时/缓存文件）:")

        ignore_dirs = self.IGNORED_DIRS.copy()
        if extra_ignore_dirs:
            ignore_dirs.update(extra_ignore_dirs)

        files: List[str] = []
        root_path = Path(self.output_dir)

        try:
            for file_path in root_path.rglob("*"):
                if not file_path.is_file():
                    continue

                # 1. 跳过配置的黑名单目录
                if any(part in ignore_dirs for part in file_path.parts):
                    continue

                # 2. 跳过 node_ 前缀等临时文件
                if file_path.name.startswith(tuple(self.IGNORED_PREFIXES)):
                    continue

                # 3. 跳过无意义扩展名
                if file_path.suffix.lower() in self.IGNORED_EXTENSIONS:
                    continue

                # 4. 隐藏文件控制
                if not include_hidden and any(part.startswith('.') for part in file_path.parts):
                    # 允许 .github, .vscode 等有意义的隐藏目录，但过滤纯隐藏文件
                    if file_path.name.startswith('.') and file_path.suffix == '':
                        continue  # 跳过 .gitignore 这种也行？看你需求
                    # 下面这行保留 .env, .gitignore 等重要隐藏文件
                    if file_path.parent == root_path and file_path.name.startswith('.'):
                        pass  # 根目录下的 .env 等保留
                    elif file_path.name.startswith('.'):
                        continue  # 子目录下的大多数 .xxx 隐藏文件都忽略

                # 5. 深度限制
                if max_depth is not None:
                    depth = len(file_path.relative_to(root_path).parts) - 1
                    if depth > max_depth:
                        continue

                rel_path = file_path.relative_to(root_path).as_posix()
                files.append(rel_path)

            sorted_files = sorted(files)

            if sorted_files:
                for f in sorted_files:
                    print(f"  - {f}")
            else:
                print("  (空目录或全部被过滤)")

            return {
                "success": True,
                "operation": "LIST_FILES",
                "files": sorted_files,
                "filtered": True,
                "note": "已自动过滤 node_modules、__pycache__、临时文件等"
            }

        except Exception as e:
            err_msg = f"列出文件失败: {e}"
            print(f"错误: {err_msg}")
            return {"success": False, "error": err_msg}


# ======================================
# 🚀 主程序示例：Agent 自主迭代循环
# ======================================

def run_agent_loop(initial_input: str, file_handler: FileOperationHandler):
    """
    模拟一个支持 AGAIN 的 Agent 循环
    实际应用中，这里会调用 LLM API 获取 response
    """
    history = []
    current_input = initial_input
    max_iterations = 5

    print("=" * 60)
    print("🤖 开始自主代理循环...")
    print("=" * 60)

    for i in range(max_iterations):
        print(f"\n🔄 第 {i+1} 轮处理:")
        print(f"📝 输入:\n{current_input}")

        follow_up_needed = False
        last_reason = ""

        def on_operation_complete(op, result):
            nonlocal follow_up_needed, last_reason
            if result.get("operation") == "AGAIN":
                follow_up_needed = True
                last_reason = result.get("reason", "未知原因")

        # 执行操作
        file_handler.handle_tagged_file_operations(current_input, callback=on_operation_complete)

        if not follow_up_needed:
            print("✅ 任务已完成，无需进一步操作。")
            break

        # 构造反馈提示
        feedback_prompt = (
            f"上一轮操作已完成。你请求继续处理，原因是：'{last_reason}'。\n"
            "请根据当前项目状态决定下一步。\n"
            "建议使用 <list_files /> 或 <read_file path=\"...\" /> 查看现有内容。\n"
        )

        # 👇 在真实系统中，这里应调用 LLM
        # 示例：new_response = llm(prompt + context + feedback_prompt)

        # 当前为模拟行为：
        if i == 0:
            current_input = (
                "<list_files />\n"
                "<again reason=\"我需要查看文件结构后再创建文档\" />"
            )
        elif i == 1:
            current_input = (
                "<create_file path=\"docs/README.md\">"
                "# Project\n\nAuto-generated by agent.\n"
                "</create_file>"
            )
        elif i == 2:
            current_input = (
                "<read_file path=\"docs/README.md\" />\n"
                "<again reason=\"确认文档已生成，准备结束\" />"
            )
        else:
            current_input = ""  # 结束

    else:
        print("⚠️  达到最大迭代次数，停止。")

    print("🏁 代理循环结束。")


# ===========================
# 💡 运行示例
# ===========================

if __name__ == "__main__":
    # 1. 显示提示词
    print(FileOperationHandler.get_file_operation_prompt())
    print("\n" + "="*60 + "\n")

    # 2. 初始化处理器
    handler = FileOperationHandler("test_output")

    # 3. 示例输入（模拟 Agent 输出）
    # test_input = (
    #     "<create_file path=\"main.py\">"
    #     "print('Hello World')"
    #     "</create_file>\n"
    #     "<again reason=\"需要先创建主