import json
import re
import os
from ai_agent_factory.agent.baseagent import BaseAgent
class SystemManagerAgent(BaseAgent):
    def __init__(self, basellm, agents):
        self.agents = agents  # 包含 pm, pj, fe, be 四个 agents
        self.project_state = {
            'prd_completed': False,
            'guides_completed': False,
            'backend_completed': False,
            'frontend_completed': False,
            'project_completed': False
        }
        system_prompt = (
            "你是一位资深的系统架构师和技术总监，负责协调整个软件开发流程。\n"
            "你的职责包括：\n"
            "1. 接收客户需求并与产品经理对话完善需求\n"
            "2. 调度各个角色（产品经理、项目经理、前后端程序员）工作\n"
            "3. 监控项目进度和质量\n"
            "4. 协调前后端对接\n"
            "5. 处理功能修改需求\n"
            "6. 确保项目按时完成\n"
            "\n工作流程：\n"
            "1. 与客户多轮对话确定需求\n"
            "2. 调度产品经理生成 PRD\n"
            "3. 调度项目经理生成指导文档\n"
            "4. 调度后端程序员开发接口和数据库\n"
            "5. 调度前端程序员开发页面\n"
            "6. 协调前后端对接\n"
            "7. 处理后续修改需求\n"
            "\n修改需求处理：\n"
            "当收到修改需求时，你应该：\n"
            "1. 先让项目经理分析影响范围\n"
            "2. 根据项目经理的分析结果调度相应角色\n"
            "\n可用操作：\n"
            "- 'ask_pm': 询问产品经理\n"
            "- 'ask_pj': 询问项目经理\n"
            "- 'ask_fe': 询问前端程序员\n"
            "- 'ask_be': 询问后端程序员\n"
            "- 'analyze_change': 让项目经理分析修改需求\n"
            "- 'modify_fe': 调度前端程序员修改\n"
            "- 'modify_be': 调度后端程序员修改\n"
            "- 'modify_both': 调度前后端程序员修改\n"
            "- 'status': 报告当前项目状态\n"
            "- 'next': 执行下一步\n"
            "- 'done': 项目完成\n"
            "\n项目目录结构：\n"
            "- 前端文件在 frontend/ 目录下\n"
            "- 后端文件在 backend/ 目录下\n"
            "- 确保前后端能够正确对接\n"
        )
        super().__init__(basellm, system_prompt, max_context=60)
    def todo(self, token: str):
        try:
            # 解析管理者的决策
            print(f"🤖 系统管理者: {token}")
            self.make_decision(token)
        except Exception as e:
            print(f"❌ 管理者决策解析错误: {e}")
            print("原始响应:", token)
    def token_deal(self, result: str):
        print(result, end='', flush=True)
    def make_decision(self, decision: str):
        """根据管理者的决策调度相应角色"""
        if "ask_pm" in decision:
            message = decision.replace("ask_pm:", "").strip()
            print(f"📋 管理者调度产品经理: {message}")
            self.agents['pm'].chat(message)
        elif "ask_pj" in decision:
            message = decision.replace("ask_pj:", "").strip()
            message +="产品文档：" + self.agents["pm"].prd;
            print(f"📋 管理者调度项目经理: {message}")
            self.agents['pj'].chat(message)
        elif "ask_fe" in decision:
            message = decision.replace("ask_fe:", "").strip()
            print(f"📋 管理者调度前端程序员: {message}")
            # 获取前端指导文档
            frontend_guide = getattr(self.agents['pj'], 'frontend_guide', {})
            if not frontend_guide:
                frontend_guide_path = os.path.join("output", "frontend_guide.md")
                if os.path.exists(frontend_guide_path):
                    try:
                        with open(frontend_guide_path, "r", encoding="utf-8") as f:
                            frontend_guide = f.read()
                    except Exception as e:
                        print(f"❌ 读取前端指导文档失败: {e}")
            # 获取API规范
            api_spec = getattr(self.agents['be'], 'api_spec', {})
            if not api_spec:
                api_spec_path = os.path.join("output", "api_spec.json")
                if os.path.exists(api_spec_path):
                    try:
                        with open(api_spec_path, "r", encoding="utf-8") as f:
                            api_spec = json.load(f)
                    except Exception as e:
                        print(f"❌ 读取API规范文件失败: {e}")
            self.agents['fe'].chat(json.dumps({
                "guide": frontend_guide,
                "project_target": message,
                "api_spec": api_spec   
            }, ensure_ascii=False))
        elif "ask_be" in decision:
            message = decision.replace("ask_be:", "").strip()
            print(f"📋 管理者调度后端程序员: {message}")
            # 获取后端指导文档
            backend_guide = getattr(self.agents['pj'], 'backend_guide')
            if not backend_guide:
                backend_guide_path = os.path.join("output", "backend_guide.md")
                if os.path.exists(backend_guide_path):
                    try:
                        with open(backend_guide_path, "r", encoding="utf-8") as f:
                            backend_guide = f.read();
                    except Exception as e:
                        print(f"❌ 读取后端指导文档失败: {e}")
            self.agents['be'].chat(json.dumps({
                "guide": backend_guide,
                "project_target": message
            }, ensure_ascii=False))
        elif "analyze_change" in decision:
            message = decision.replace("analyze_change:", "").strip()
            print(f"📋 管理者让项目经理分析修改需求: {message}")
            self.agents['pj'].chat(f"请分析以下修改需求的影响范围，告诉我需要前端还是后端修改：\n{message}")
            analysis_result = self.agents['pj'].analysis_result
            if analysis_result:
                # 根据分析结果调度相应角色
                if "modify_fe:" in analysis_result:
                    # 调度前端程序员修改
                    self.make_decision(f"modify_fe: {message}")
                elif "modify_be:" in analysis_result:
                    # 调度后端程序员修改
                    self.make_decision(f"modify_be: {message}")
                elif "both_modify:" in analysis_result:
                    # 调度前后端程序员修改
                    self.make_decision(f"modify_both: {message}")
            
            # 注意：这里不应该直接调用make_decision，应该等待项目经理的回复
        elif "modify_fe" in decision:
            message = decision.replace("modify_fe:", "").strip()
            print(f"🔧 管理者调度前端程序员修改: {message}")
            # 获取API规范用于前端修改
            api_spec = None;
            if not api_spec:
                api_spec_path = os.path.join("output", "api_spec.json")
                if os.path.exists(api_spec_path):
                    try:
                        with open(api_spec_path, "r", encoding="utf-8") as f:
                            api_spec = json.load(f)
                    except Exception as e:
                        print(f"❌ 读取API规范文件失败: {e}")
            self.agents['fe'].chat(json.dumps({
                "project_target": f"根据以下修改需求更新前端页面:\n{message}",
                "api_spec": api_spec
            }, ensure_ascii=False))
            # 重置完成状态以便重新检查
            self.project_state['frontend_completed'] = False
        elif "modify_be" in decision:
            message = decision.replace("modify_be:", "").strip()
            print(f"🔧 管理者调度后端程序员修改: {message}")
            self.agents['be'].chat(json.dumps({
                "project_target": f"根据以下修改需求更新后端服务:\n{message}"
            }, ensure_ascii=False))
            # 重置完成状态以便重新检查
            self.project_state['backend_completed'] = False
        elif "modify_both" in decision:
            message = decision.replace("modify_both:", "").strip()
            print(f"🔧 管理者调度前后端程序员修改: {message}")
            # 获取API规范
            api_spec = getattr(self.agents['be'], 'api_spec', {})
            if not api_spec:
                api_spec_path = os.path.join("output", "api_spec.json")
                if os.path.exists(api_spec_path):
                    try:
                        with open(api_spec_path, "r", encoding="utf-8") as f:
                            api_spec = json.load(f)
                    except Exception as e:
                        print(f"❌ 读取API规范文件失败: {e}")
            self.agents['be'].chat(json.dumps({
                "project_target": f"根据以下修改需求更新后端服务:\n{message}"
            }, ensure_ascii=False))
            self.agents['fe'].chat(json.dumps({
                "project_target": f"根据以下修改需求更新前端服务:\n{message}",
                "api_spec": api_spec
            }, ensure_ascii=False))
            # 重置完成状态以便重新检查
            self.project_state['backend_completed'] = False
            self.project_state['frontend_completed'] = False
        elif "status" in decision:
            self.report_status()
        elif "next" in decision:
            self.execute_next_step()
        elif "done" in decision:
            print("🎉 项目开发完成！")
            self.project_state['project_completed'] = True
            self.report_final_status()
        else:
            print(f"⚠️  未知决策: {decision}")
    def handle_change_request(self, request: str):
        """处理修改需求 - 直接让项目经理分析"""
        print(f"🔄 收到修改需求: {request}")
        # 让项目经理分析需求影响范围
        self.make_decision(f"analyze_change: {request}")
    def report_status(self):
        """报告项目当前状态"""
        print("\n📊 项目状态报告:")
        status_icon = "✅" if self.project_state['prd_completed'] else "⏳"
        print(f"{status_icon} 产品经理: {'PRD 已完成' if self.project_state['prd_completed'] else '进行中'}")
        status_icon = "✅" if self.project_state['guides_completed'] else "⏳"
        print(f"{status_icon} 项目经理: {'指导文档已完成' if self.project_state['guides_completed'] else '进行中'}")
        status_icon = "✅" if self.project_state['backend_completed'] else "⏳"
        print(f"{status_icon} 后端程序员: {'接口开发已完成' if self.project_state['backend_completed'] else '进行中'}")
        status_icon = "✅" if self.project_state['frontend_completed'] else "⏳"
        print(f"{status_icon} 前端程序员: {'页面开发已完成' if self.project_state['frontend_completed'] else '进行中'}")
        status_icon = "✅" if self.project_state['project_completed'] else "⏳"
        print(f"{status_icon} 项目整体: {'已完成' if self.project_state['project_completed'] else '进行中'}")
    def execute_next_step(self):
        """执行下一步开发任务"""
        # 检查项目进度并决定下一步
        if not self.project_state['prd_completed']:
            print("📋 管理者: 调度产品经理生成 PRD")
            self.agents['pm'].chat(f"请根据客户需求生成详细的产品需求文档：\n{json.dumps(self.get_context(),ensure_ascii=False)}")
            self.project_state['prd_completed'] = True
        elif not self.project_state['guides_completed']:
            print("📋 管理者: 调度项目经理生成指导文档")
            prd = getattr(self.agents['pm'], 'prd', 'PRD 内容')
            self.agents['pj'].chat(f"根据以下 PRD 生成开发指导文档:\n{prd}")
            self.project_state['guides_completed'] = True
        elif not self.project_state['backend_completed']:
            print("📋 管理者: 调度后端程序员开发接口")
            # 从项目经理代理获取后端指导文档
            backend_guide = getattr(self.agents['pj'], 'backend_guide', {})
            # 如果没有，尝试从文件读取
            if not backend_guide:
                backend_guide_path = os.path.join("output", "backend_guide.json")
                if os.path.exists(backend_guide_path):
                    try:
                        with open(backend_guide_path, "r", encoding="utf-8") as f:
                            backend_guide = json.load(f)
                    except Exception as e:
                        print(f"❌ 读取后端指导文档失败: {e}")
            prd = getattr(self.agents['pm'], 'prd', 'PRD 内容')
            self.agents['be'].chat(json.dumps({
                "guide": backend_guide,
                "project_target": prd
            }, ensure_ascii=False))
            self.project_state['backend_completed'] = True
        elif not self.project_state['frontend_completed']:
            print("📋 管理者: 调度前端程序员开发页面")
            # 从项目经理代理获取前端指导文档
            frontend_guide = getattr(self.agents['pj'], 'frontend_guide', {})
            # 如果没有，尝试从文件读取
            if not frontend_guide:
                frontend_guide_path = os.path.join("output", "frontend_guide.md")
                if os.path.exists(frontend_guide_path):
                    try:
                        with open(frontend_guide_path, "r", encoding="utf-8") as f:
                            frontend_guide = f.read();
                    except Exception as e:
                        print(f"❌ 读取前端指导文档失败: {e}")
            prd = getattr(self.agents['pm'], 'prd', 'PRD 内容')
            # 获取API规范
            api_spec = getattr(self.agents['be'], 'api_spec', {})
            # 如果没有，尝试从文件读取
            if not api_spec:
                api_spec_path = os.path.join("output", "api_spec.json")
                if os.path.exists(api_spec_path):
                    try:
                        with open(api_spec_path, "r", encoding="utf-8") as f:
                            api_spec = json.load(f)
                    except Exception as e:
                        print(f"❌ 读取API规范文件失败: {e}")
            self.agents['fe'].chat(json.dumps({
                "guide": frontend_guide,
                "project_target": prd,
                "api_spec": api_spec
            }, ensure_ascii=False))
            self.project_state['frontend_completed'] = True
        else:
            print("📋 管理者: 项目已完成，等待修改需求")
    def report_final_status(self):
        """报告最终项目状态"""
        print("\n🎯 最终项目成果:")
        print("📁 输出文件:")
        print("  - frontend/ 目录: 前端页面文件")
        print("  - backend/ 目录: 后端文件")
        print("  - api_spec.json: 接口文档")
        print("  - frontend_guide.json: 前端开发指导")
        print("  - backend_guide.json: 后端开发指导")
        print("  - 其他相关文件...")
# http://localhost:5173/api/v1/auth/register 404了

"""


"""