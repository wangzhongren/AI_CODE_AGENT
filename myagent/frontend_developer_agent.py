# frontend_developer_agent.py (修复版)
import json
import re
import os
from ai_agent_factory.agent.baseagent import BaseAgent
from ai_agent_factory.utils.file_operation_handler import FileOperationHandler
fo = FileOperationHandler()
class FrontendDeveloperAgent(BaseAgent):
    def __init__(self, basellm):
        system_prompt = (
"🎨 你是一位兼具技术实力与卓越审美能力的专业前端程序员，精通 HTML、CSS、vue、vite、vuetify 等前端常用的框架\n"
"你对现代网页设计有深刻理解，追求极简、优雅、用户友好的界面风格。\n"
"你需要根据项目经理的需求和接口文档，开发完整且视觉出众的前端页面。\n"
"\n你的职责包括：\n"
"1. 根据需求动态规划页面结构与数量\n"
"2. 实现流畅的页面间导航与微交互\n"
"3. 正确调用后端 API 并处理数据展示\n"
"4. 创建清晰合理的文件组织结构\n"
"\n✨ 设计原则（必须遵守）：\n"
"• 极简主义：去除一切非必要元素，保持界面干净清爽\n"
"• 留白艺术：合理使用 padding/margin，让内容自然呼吸\n"
"• 色彩和谐：主色调不超过 3 种，推荐浅灰/蓝白/莫兰迪系，禁止荧光色\n"
"• 字体优雅：优先使用系统默认无衬线字体（如 -apple-system, BlinkMacSystemFont, sans-serif）\n"
"• 响应式布局：适配桌面与移动端，优先采用 flex 或 grid 布局\n"
"• 视觉层次：通过字号、字重、颜色清晰区分标题、正文与操作元素\n"
"• 交互反馈：按钮必须有 hover/active 状态，链接需有下划线或颜色变化等视觉提示\n"
"• 居中美学：主要内容区域居中显示，最大宽度建议不超过 800px\n"

"\n⚠️ 禁止行为：\n"
"• 不得使用 Bootstrap、Tailwind 等第三方 CSS 框架\n"
"• 不得内联大量样式（样式应集中于外部 CSS 文件）\n"
"• 不得使用过时或非语义化标签（如 <center>, <font>）\n"
"• 不得忽略可访问性（如图片必须包含 alt 属性）\n"
) + fo.get_file_operation_prompt()
        super().__init__(basellm, system_prompt, max_context=50)
        self.files = []
        self.output_dir = "output"
    def todo(self, token: str):
        try:
            is_need_loop = [False];
            # is_need_loop[0] = False;
            need_data = [];
            print(f"🔍 收到前端开发响应，长度: {len(token)} 字符")
            # 检查是否包含文件操作标记
            if FileOperationHandler.has_file_operations(token):
                print("✅ 检测到文件操作指令")
                is_need_loop[0] = True;
                def callback(op,result):
                    # if result["operation"] == "AGAIN":
                    # else:
                        need_data.append(result);
                fo.handle_tagged_file_operations(token,callback)
                
            if is_need_loop[0]:
                self.chat(json.dumps(need_data,ensure_ascii=False))
            print(f"📝 前端程序员回复: {token}")
        except Exception as e:
            print(f"\n❌ 前端开发失败: {e}")
            import traceback
            traceback.print_exc()
            print("原始响应:", token)
    def token_deal(self, result: str):
        print(result, end='', flush=True)
    def handle_tagged_file_operations(self, token: str) -> bool:
        """处理带标记的文件操作指令"""
        try:
            # 提取所有 <FILE_OP> 标记内的指令
            pattern = r'<FILE_OP>(.*?)</FILE_OP>'
            operations = re.findall(pattern, token, re.DOTALL)
            if not operations:
                print("⚠️  未找到有效的文件操作指令")
                return False
            print(f"🔄 找到 {len(operations)} 个文件操作指令")
            for i, op in enumerate(operations):
                op = op.strip()
                print(f"  [{i+1}] 执行: {op[:100]}{'...' if len(op) > 100 else ''}")
                # 处理单个操作
                self.handle_single_operation(op)
            print("✅ 文件操作完成")
            return True
        except Exception as e:
            print(f"❌ 文件操作失败: {e}")
            import traceback
            traceback.print_exc()
        return False
    def handle_single_operation(self, op: str):
        """处理单个文件操作"""
        if op.startswith("CREATE_FILE:"):
            # 处理 CREATE_FILE 操作
            try:
                # 分割指令，但要考虑内容中可能包含冒号
                parts = op[12:].split(":")
                if len(parts) >= 2:
                    filename = parts[0]
                    content = ":".join(parts[1:])  # 将剩余部分重新组合为内容
                    self.create_file(filename.strip(), content.strip())
                else:
                    # 尝试另一种解析方式，适用于多行内容
                    match = re.match(r'CREATE_FILE:\s*(.+?)\s*:(.*)', op, re.DOTALL)
                    if match:
                        filename = match.group(1).strip()
                        content = match.group(2).strip()
                        self.create_file(filename, content)
                    else:
                        print(f"❌ CREATE_FILE 指令格式错误: {op}")
            except Exception as e:
                print(f"❌ 处理 CREATE_FILE 指令失败: {e}")
        elif op.startswith("READ_FILE:"):
            filename = op[10:].strip()
            self.read_file(filename)
        elif op.startswith("UPDATE_FILE:"):
            # 处理 UPDATE_FILE 操作
            try:
                parts = op[12:].split(":")
                if len(parts) >= 2:
                    filename = parts[0]
                    content = ":".join(parts[1:])
                    self.update_file(filename.strip(), content.strip())
                else:
                    match = re.match(r'UPDATE_FILE:\s*(.+?)\s*:(.*)', op, re.DOTALL)
                    if match:
                        filename = match.group(1).strip()
                        content = match.group(2).strip()
                        self.update_file(filename, content)
                    else:
                        print(f"❌ UPDATE_FILE 指令格式错误: {op}")
            except Exception as e:
                print(f"❌ 处理 UPDATE_FILE 指令失败: {e}")
        elif op.startswith("DELETE_FILE:"):
            filename = op[12:].strip()
            self.delete_file(filename)
        elif op == "LIST_FILES":
            self.list_files()
        elif op.startswith("BATCH_OPERATIONS:"):
            # 处理批量操作
            batch_ops = op[17:].split(";")
            for batch_op in batch_ops:
                batch_op = batch_op.strip()
                if batch_op:
                    self.handle_single_operation(batch_op)
        else:
            print(f"⚠️  未知操作类型: {op[:50]}{'...' if len(op) > 50 else ''}")
    def handle_json_task(self, token: str) -> bool:
        """处理 JSON 格式的项目开发任务"""
        try:
            # 检查是否包含 JSON 格式
            if "```json" in token or '"files":' in token:
                # 去除 Markdown 代码块标记
                json_str = re.sub(r'^```[a-z]*\s*', '', token.strip())
                json_str = re.sub(r'```$', '', json_str).strip()
                # 解析 JSON
                result = json.loads(json_str)
                files = result["files"]
                # 保存生成的文件列表
                self.files = files
                # 创建目录并保存所有文件
                for file_info in files:
                    filename = file_info["filename"]
                    content = file_info["content"]
                    # 确保文件路径在 output 目录下
                    full_path = os.path.join(self.output_dir, filename)
                    # 规范化路径
                    full_path = os.path.normpath(full_path)
                    if not full_path.startswith(self.output_dir + os.sep):
                        print(f"❌ 文件路径无效: {filename}")
                        continue
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    # 写入文件
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"✅ 前端文件已保存: {full_path}")
                print(f"\n✅ 前端开发完成，共生成 {len(files)} 个文件")
                # 统计文件类型
                file_types = {}
                for file_info in files:
                    ext = file_info["filename"].split(".")[-1] if "." in file_info["filename"] else "no_ext"
                    file_types[ext] = file_types.get(ext, 0) + 1
                print("📁 文件类型统计:", file_types)
                return True
        except Exception as e:
            print(f"⚠️  JSON任务处理失败: {e}")
        return False
    def create_file(self, filename: str, content: str):
        """创建文件"""
        print(f"📁 创建文件: {filename}")
        # 确保文件路径在 output 目录下
        full_path = os.path.join(self.output_dir, filename)
        # 规范化路径，防止路径遍历攻击
        full_path = os.path.normpath(full_path)
        if not full_path.startswith(self.output_dir + os.sep):
            print(f"❌ 文件路径无效: {filename}")
            return
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ 文件已创建: {full_path}")
        except Exception as e:
            print(f"❌ 创建文件失败: {e}")
    def read_file(self, filename: str):
        """读取文件"""
        print(f"📖 读取文件: {filename}")
        # 确保文件路径在 output 目录下
        full_path = os.path.join(self.output_dir, filename)
        # 规范化路径
        full_path = os.path.normpath(full_path)
        if not full_path.startswith(self.output_dir + os.sep):
            print(f"❌ 文件路径无效: {filename}")
            return
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"📄 文件内容 ({filename}):\n{content}")
        except FileNotFoundError:
            print(f"❌ 文件不存在: {full_path}")
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
    def update_file(self, filename: str, content: str):
        """更新文件"""
        print(f"✏️  更新文件: {filename}")
        # 确保文件路径在 output 目录下
        full_path = os.path.join(self.output_dir, filename)
        # 规范化路径
        full_path = os.path.normpath(full_path)
        if not full_path.startswith(self.output_dir + os.sep):
            print(f"❌ 文件路径无效: {filename}")
            return
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ 文件已更新: {full_path}")
        except Exception as e:
            print(f"❌ 更新文件失败: {e}")
    def delete_file(self, filename: str):
        """删除文件"""
        print(f"🗑️  删除文件: {filename}")
        # 确保文件路径在 output 目录下
        full_path = os.path.join(self.output_dir, filename)
        # 规范化路径
        full_path = os.path.normpath(full_path)
        if not full_path.startswith(self.output_dir + os.sep):
            print(f"❌ 文件路径无效: {filename}")
            return
        try:
            os.remove(full_path)
            print(f"✅ 文件已删除: {full_path}")
        except FileNotFoundError:
            print(f"❌ 文件不存在: {full_path}")
        except Exception as e:
            print(f"❌ 删除文件失败: {e}")
    def list_files(self):
        """列出所有文件"""
        print("📂 列出所有文件:")
        try:
            files = []
            for root, dirs, filenames in os.walk(self.output_dir):
                for filename in filenames:
                    full_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(full_path, self.output_dir)
                    files.append(relative_path)
            print("📁 项目文件列表:")
            for file in sorted(files):
                print(f"  - {file}")
        except Exception as e:
            print(f"❌ 列出文件失败: {e}")