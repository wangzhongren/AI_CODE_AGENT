import json
import re
import os
from ai_agent_factory.agent.baseagent import BaseAgent
from ai_agent_factory.utils.file_operation_handler import FileOperationHandler
# fo = FileOperationHandler()
class ProjectManagerAgent(BaseAgent):
    def __init__(self, basellm):
        fo = FileOperationHandler(llm=basellm)
        self.fo = fo;
        system_prompt = (
            "你是一位经验丰富的项目经理，负责协调前后端开发工作。\n"
            "你需要根据产品经理提供的 PRD 文档，生成三个关键文档：\n"
            "1. 前端开发指导文档：包括页面结构、文件名、需要调用的接口等\n"
            "2. 后端开发指导文档：包括接口路径、请求方式、参数、返回值结构、数据库设计等\n"
            "3. 前后端对接文档：包括接口调用示例、Mock 数据、联调方式等\n"
            "\n项目目录结构要求：\n"
            "- 前端文件必须放在 frontend/ 目录下\n"
            "- 后端文件必须放在 backend/ 目录下\n"
            "- 确保前后端能够正确对接\n"
            "\n前端开发指导要求：\n"
            "- 根据 PRD 动态确定需要的页面数量和类型\n"
            "- 每个页面需要说明功能和需要调用的接口\n"
            "- 页面间需要有导航关系\n"
            "- 列表页必须考虑分页功能\n"
            "- 详情页必须能根据 ID 获取数据\n"
            "- 表单页需要包含数据提交功能\n"
            "- 必须考虑不同前端框架的目录结构差异：\n"
            "  * 普通 HTML+CSS 项目：所有页面文件放在 frontend/public/ 目录下\n"
            "  * Vue 项目：遵循 Vue CLI 项目结构，组件放在 frontend/src/components/，页面放在 frontend/src/views/\n"
            "  * React 项目：遵循 Create React App 项目结构，组件放在 frontend/src/components/\n"
            "  * 根据项目复杂度选择合适的框架，简单项目用 HTML+CSS，复杂项目用 Vue 或 React\n"
            "\n后端开发指导要求：\n"
            "- 必须包含数据库表设计（建表语句）\n"
            "- 接口必须支持分页、参数校验\n"
            "- 返回值必须包含完整的数据结构\n"
            "- 必须配置静态文件服务以正确提供前端文件：\n"
            "  * 普通项目：app.use(express.static(path.join(__dirname, '../frontend/public')))\n"
            "  * Vue/React 构建项目：app.use(express.static(path.join(__dirname, '../frontend/dist')))\n"
            "\n前后端对接要求：\n"
            "- 明确指定 API 基础路径（如 /api/v1/）\n"
            "- 确保跨域配置正确\n"
            "- 提供完整的接口调用示例\n"
            "- 明确前后端目录结构和文件路径\n"
            "\n另外，当需要分析修改需求时，请回答：\n"
            "- 'modify_fe: 具体修改内容' (如果只需要前端修改)\n"
            "- 'modify_be: 具体修改内容' (如果只需要后端修改)\n"
            "- 'both_modify: 前端需要... 后端需要...' (如果前后端都需要修改)\n"
            "- 'need_more_info: 需要更多信息' (如果需求不明确)\n"
            "\n请使用文件操作指令来创建以下文件：\n"
            "- 创建 frontend_guide.md 文件存储前端开发指导\n"
            "- 创建 backend_guide.md 文件存储后端开发指导\n"
            "- 创建 integration_doc.md 文件存储对接文档\n"
            "\n重要注意事项：\n"
            "1. 前端文件路径必须与后端静态文件服务配置匹配\n"
            "2. Vue/React 项目需要考虑构建后的文件位置（frontend/dist/ 目录）\n"
            "3. 确保 API 路径在前后端之间保持一致\n"
            "4. 考虑开发环境和生产环境的差异\n"
            "5. 严格遵循 frontend/ 和 backend/ 的目录分离结构\n"

        )+fo.get_file_operation_prompt()
        super().__init__(basellm, system_prompt, max_context=50)
        # 用于存储分析结果
        self.analysis_result = None
        self.frontend_guide = None
        self.backend_guide = None
        self.integration_doc = None
        self.output_dir = "output"
    def todo(self, token: str):
        try:
            print(f"🔍 收到项目经理响应，长度: {len(token)} 字符")
            # 首先检查是否是修改需求分析请求
            if "modify_fe:" in token or "modify_be:" in token or "both_modify:" in token or "need_more_info:" in token:
                print(f"📋 项目经理分析结果: {token}")
                self.analysis_result = token
                return
            # 检查是否包含文件操作标记
            # if fo.handle_tagged_file_operations(token=token):
            #     print("✅ 检测到文件操作指令");

            is_need_loop = False;
            need_data = [];
            def callback(op,result):
                    # is_need_loop[0] = True;
                    need_data.append(result);
            if FileOperationHandler.has_file_operations(token):
                is_need_loop = True;
                print("✅ 检测到文件操作指令")
                if self.fo.handle_tagged_file_operations(token,callback):
                    # 处理完文件操作后，确保加载相关文档
                    self.load_guides_from_files()
                    return
            # 如果没有文件操作指令，当作普通文本处理
            print(f"📝 项目经理回复: {token}")
            if is_need_loop:
                self.chat(json.dumps(need_data,ensure_ascii=False))
        except Exception as e:
            print(f"\n❌ 项目经理任务失败: {e}")
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
    def load_guides_from_files(self):
        """从文件加载指导文档"""
        print("🔍 从文件加载指导文档...")
        # 尝试加载前端指导文档
        frontend_guide_path = os.path.join(self.output_dir, "frontend_guide.md")
        if os.path.exists(frontend_guide_path):
            try:
                with open(frontend_guide_path, "r", encoding="utf-8") as f:
                    self.frontend_guide = f.read()
                print("✅ 已加载前端指导文档")
            except Exception as e:
                print(f"❌ 加载前端指导文档失败: {e}")
        # 尝试加载后端指导文档
        backend_guide_path = os.path.join(self.output_dir, "backend_guide.md")
        if os.path.exists(backend_guide_path):
            try:
                with open(backend_guide_path, "r", encoding="utf-8") as f:
                    self.backend_guide = f.read()
                print("✅ 已加载后端指导文档")
            except Exception as e:
                print(f"❌ 加载后端指导文档失败: {e}")
        # 尝试加载对接文档
        integration_doc_path = os.path.join(self.output_dir, "integration_doc.md")
        if os.path.exists(integration_doc_path):
            try:
                with open(integration_doc_path, "r", encoding="utf-8") as f:
                    self.integration_doc = f.read();
                print("✅ 已加载对接文档")
            except Exception as e:
                print(f"❌ 加载对接文档失败: {e}")
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
            # 如果创建的是指导文档文件，保存其内容
            if filename == "frontend_guide.md":
                try:
                    self.frontend_guide = content;
                    print("✅ 前端指导文档已加载到内存")
                except Exception as e:
                    print(f"⚠️  解析前端指导文档失败: {e}")
            elif filename == "backend_guide.md":
                try:
                    self.backend_guide = content;
                    print("✅ 后端指导文档已加载到内存")
                except Exception as e:
                    print(f"⚠️  解析后端指导文档失败: {e}")
            elif filename == "integration_doc.md":
                try:
                    self.integration_doc = content;
                    print("✅ 对接文档已加载到内存")
                except Exception as e:
                    print(f"⚠️  解析对接文档失败: {e}")
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
            # 如果更新的是指导文档文件，保存其内容
            if filename == "frontend_guide.md":
                try:
                    self.frontend_guide = content;
                    print("✅ 前端指导文档已更新到内存")
                except Exception as e:
                    print(f"⚠️  解析前端指导文档失败: {e}")
            elif filename == "backend_guide.md":
                try:
                    self.backend_guide = content
                    print("✅ 后端指导文档已更新到内存")
                except Exception as e:
                    print(f"⚠️  解析后端指导文档失败: {e}")
            elif filename == "integration_doc.md":
                try:
                    self.integration_doc = content
                    print("✅ 对接文档已更新到内存")
                except Exception as e:
                    print(f"⚠️  解析对接文档失败: {e}")
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