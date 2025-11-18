import json
import re
import os
from ai_agent_factory.agent.baseagent import BaseAgent
from ai_agent_factory.llms.base_llm_openai import OpenAILLM
from ai_agent_factory.utils.file_operation_handler import FileOperationHandler

class BackendDeveloperAgent(BaseAgent):

    def __init__(self, basellm):
        fo = FileOperationHandler(llm=basellm)
        self.fo  = fo;
        system_prompt = (
            "你是一位专业的全栈后端程序员兼数据库工程师，精通 Node.js、Express 框架和数据库设计。\n"
            "你需要根据项目经理提供的指导，完成完整的后端开发工作。\n"
            "\n你的职责包括：\n"
            "1. 设计数据库表结构（MySQL/PostgreSQL/Sqlite）\n"
            "2. 实现完整的 API 服务\n"
            "3. 生成详细的 OpenAPI 接口文档\n"
            "4. 配置静态文件服务（自动暴露 public 目录）\n"
            "5. 根据实际需求创建必要的文件结构\n"
            "\n重要要求：\n"
            "1. 必须在主服务文件中添加静态文件服务配置：app.use(express.static('public'))\n"
            "2. 前端生成的所有文件都在 public 目录下，后端需要正确提供这些静态文件\n"
            "3. 数据库设计必须包含建表语句（CREATE TABLE）\n"
            "4. 支持分页、参数校验、错误处理\n"
            "5. 接口文档使用 OpenAPI 3.0 格式\n"
            "6. 根据实际接口数量和复杂度决定文件组织结构\n"
            "7. 可以创建任意必要的文件（如：models, middleware, utils 等）\n"
            "8. 必须创建 **api_spec.json** 文件来存储所有接口说明\n"
            "9. api_spec.json 文件直接放在根目录\n"
            "10. 项目其他文件放入backend文件夹下"
            "11. 你只需要编写后端代码\n"
            "\n文件操作指令支持：\n"
        )+ fo.get_file_operation_prompt();
        super().__init__(basellm, system_prompt, max_context=50)
        self.api_spec = None
        self.files = []
        self.output_dir = "output"
    def todo(self, token: str):
        try:
            # is_need_loop[0] = False;
            need_data = [];
            print(f"🔍 收到后端开发响应，长度: {len(token)} 字符")
            # 检查是否包含文件操作标记
            if FileOperationHandler.has_file_operations(token):
                print("✅ 检测到文件操作指令")
                def callback(op,result):
                    need_data.append(result);
                result = self.fo.handle_tagged_file_operations(token,callback);
                self.chat(json.dumps(need_data,ensure_ascii=False))
                if result:
                    # 处理完文件操作后，确保 api_spec.json 已生成
                    self.ensure_api_spec_file()
                    return
                
            else:
                print("⚠️  未检测到文件操作指令")
                # 即使没有文件操作指令，也尝试查找API规范
                self.extract_api_spec_from_response(token)
            # print(f"📝 后端程序员回复: {token}")
                
            # 如果没有文件操作指令，当作普通文本处理
            
        except Exception as e:
            print(f"\n❌ 后端开发失败: {e}")
            import traceback
            traceback.print_exc()
            print("原始响应:", token)
    def token_deal(self, result: str):
        print(result, end='', flush=True)
    def extract_api_spec_from_response(self, token: str):
        """从响应中提取API规范"""
        # 尝试从响应中提取JSON格式的API规范
        try:
            # 查找可能的JSON块
            json_pattern = r'```json\s*({.*?})\s*```'
            match = re.search(json_pattern, token, re.DOTALL)
            if match:
                json_str = match.group(1)
                data = json.loads(json_str)
                # 如果包含API规范相关信息
                if "paths" in data or "components" in data or "openapi" in data:
                    self.api_spec = data
                    print("✅ 从响应中提取到API规范")
        except Exception as e:
            print(f"⚠️  提取API规范失败: {e}")
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
    def ensure_api_spec_file(self):
        """确保 api_spec.json 文件已生成"""
        print("🔍 检查API规范文件...")
        # 如果已经有api_spec内容但没有生成文件，则创建文件
        if self.api_spec:
            api_spec_path = os.path.join(self.output_dir, "api_spec.json")
            # 检查文件是否已存在
            if not os.path.exists(api_spec_path):
                print("🔄 生成API规范文件...")
                os.makedirs(self.output_dir, exist_ok=True)
                try:
                    with open(api_spec_path, "w", encoding="utf-8") as f:
                        json.dump(self.api_spec, f, ensure_ascii=False, indent=2)
                    print(f"✅ API规范文件已保存: {api_spec_path}")
                except Exception as e:
                    print(f"❌ 保存API规范文件失败: {e}")
            else:
                print("✅ API规范文件已存在")
        else:
            # 如果没有api_spec内容，尝试从已创建的文件中读取
            api_spec_path = os.path.join(self.output_dir, "api_spec.json")
            if os.path.exists(api_spec_path):
                try:
                    with open(api_spec_path, "r", encoding="utf-8") as f:
                        self.api_spec = json.load(f)
                    print("✅ 已从文件加载API规范")
                except Exception as e:
                    print(f"❌ 读取API规范文件失败: {e}")
            else:
                print("⚠️  没有API规范内容且文件不存在")
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
            # 如果创建的是API规范文件，保存其内容
            if "api_spec" in filename and filename.endswith(".json"):
                try:
                    self.api_spec = json.loads(content)
                    print("✅ API规范已加载到内存")
                except Exception as e:
                    print(f"⚠️  解析API规范失败: {e}")
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
            # 如果更新的是API规范文件，保存其内容
            if "api_spec" in filename and filename.endswith(".json"):
                try:
                    self.api_spec = json.loads(content)
                    print("✅ API规范已更新到内存")
                except Exception as e:
                    print(f"⚠️  解析API规范失败: {e}")
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

if __name__ == "__main__":
    llm = OpenAILLM(
        api_key="sk-",
        model_name="qwen3-max",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    a = """
    创建一个文件A.json,里面写入如下内容
    aaa
    bbb
    cccc
    ddd
    c3ee
    print(111);
    """
    BackendDeveloperAgent(llm).chat(a);