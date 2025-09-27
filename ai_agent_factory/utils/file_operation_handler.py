import re
import os

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

           
        )

    def __init__(self, output_dir="output"):
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
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
    
    def handle_tagged_file_operations(self, token: str, callback=None) -> bool:
        """
        提取并执行所有结构化标签指令
        :param token: 包含 <tag>...</tag> 的字符串
        :param callback: 回调函数 callback(op_dict, result)
        :return: 是否至少处理了一个操作
        """
        try:
            operations = parse_structured_operations(token)
            if not operations:
                return False

            print(f"🔄 找到 {len(operations)} 个结构化操作指令")
            for i, op in enumerate(operations):
                print(f"  [{i+1}] 执行: {op['operation']} → {op.get('attributes', {}).get('path', '')}")
                result = self.execute_operation(op)
                if callback:
                    callback(op, result)
            print("✅ 操作完成")
            return True
        except Exception as e:
            print(f"❌ 解析或执行错误: {e}")
            import traceback
            traceback.print_exc()
            return False

    def execute_operation(self, op_dict: dict):
        """执行单个结构化操作"""
        op = op_dict["operation"]
        attrs = op_dict["attributes"]
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

    def list_files(self):
        """列出 output 目录下的所有文件"""
        print("📂 列出项目文件:")
        try:
            files = []
            for root, dirs, filenames in os.walk(self.output_dir):
                for fname in filenames:
                    full_path = os.path.join(root, fname)
                    rel_path = os.path.relpath(full_path, self.output_dir)
                    files.append(rel_path)
            sorted_files = sorted(files)
            if sorted_files:
                for file in sorted_files:
                    print(f"  - {file}")
            else:
                print("  (空目录)")
            return {
                "success": True,
                "operation": "LIST_FILES",
                "files": sorted_files
            }
        except Exception as e:
            err_msg = f"列出文件失败: {e}"
            print(f"❌ {err_msg}")
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