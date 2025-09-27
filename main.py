import json
import os
from ai_agent_factory.llms.base_llm_openai import OpenAILLM
from myagent.product_manager_agent import ProductManagerAgent
from myagent.frontend_developer_agent import FrontendDeveloperAgent
from myagent.backend_developer_agent import BackendDeveloperAgent
from myagent.project_manager_agent import ProjectManagerAgent
from dotenv import load_dotenv
load_dotenv()

def main():
    # 初始化 LLM
    llm = OpenAILLM(
        api_key=os.getenv('api_key'),
        model_name=os.getenv('model_name'),
        base_url=os.getenv('base_url')
    )
    # 创建 Agents
    pm_agent = ProductManagerAgent(llm)
    pj_agent = ProjectManagerAgent(llm)
    fe_agent = FrontendDeveloperAgent(llm)
    be_agent = BackendDeveloperAgent(llm)
    print("🚀 交互式项目开发系统")
    print("=" * 50)
    while True:
        try:
            # ========================
            # 1. 与产品经理多轮对话
            # ========================
            print("\n📝 产品经理对话阶段")
            print("请输入您的需求，可以多轮对话：")
            print("  - 输入需求内容进行对话")
            print("  - 输入 'done' 结束对话并开始开发")
            print("  - 输入 'quit' 退出系统")
            print("-" * 30)
            # 重置产品经理上下文
            pm_agent.reset_context()
            prd_content = ""
            while True:
                pm_input = input("[产品经理对话] >>> ").strip()
                if pm_input.lower() == "quit":
                    print("👋 再见！")
                    return
                elif pm_input.lower() == "done":
                    # 检查是否有PRD内容
                    if hasattr(pm_agent, 'prd') and pm_agent.prd:
                        prd_content = pm_agent.prd
                        break
                    elif len(pm_agent._BaseAgent__context) > 1:  # 至少有一个用户输入
                        # 从上下文中提取PRD内容
                        prd_content = "\n".join([msg['content'] for msg in pm_agent._BaseAgent__context[1:] if msg['role'] == 'assistant'])
                        break
                    else:
                        print("❌ 请先提供一些需求内容")
                        continue
                elif not pm_input:
                    continue
                else:
                    print("产品经理正在思考...")
                    pm_agent.chat(pm_input)
                    # 显示产品经理的回复
                    print(f"产品经理: {pm_agent._BaseAgent__context[-1]['content'][:100]}...")
            print("✅ 需求收集完成")
            print("PRD 内容预览:")
            print(prd_content[:200] + "..." if len(prd_content) > 200 else prd_content)
            # ========================
            # 2. 自动执行后续开发流程
            # ========================
            print("\n" + "=" * 50)
            print("🤖 开始自动开发流程...")
            # 项目经理生成指导文档
            print("\n📋 项目经理正在生成指导文档...")
            pj_agent.chat(f"根据以下 PRD 生成前后端开发指导文档：\n{prd_content}")
            # 从项目经理代理获取指导文档
            frontend_guide = pj_agent.frontend_guide
            backend_guide = pj_agent.backend_guide
            # 如果项目经理代理没有正确设置指导文档，尝试从文件读取
            if not frontend_guide:
                frontend_guide_path = os.path.join("output", "frontend_guide.md")
                if os.path.exists(frontend_guide_path):
                    try:
                        with open(frontend_guide_path, "r", encoding="utf-8") as f:
                            frontend_guide = f.read();
                    except Exception as e:
                        print(f"❌ 读取前端指导文档失败: {e}")
            if not backend_guide:
                backend_guide_path = os.path.join("output", "backend_guide.md")
                if os.path.exists(backend_guide_path):
                    try:
                        with open(backend_guide_path, "r", encoding="utf-8") as f:
                            backend_guide = f.read();
                    except Exception as e:
                        print(f"❌ 读取后端指导文档失败: {e}")
            print("✅ 指导文档已生成")
            # if frontend_guide:
            #     print(f"  - 前端页面数量: {len(frontend_guide.get('pages', []))}")
            # if backend_guide:
            #     print(f"  - 后端接口数量: {len(backend_guide.get('apis', []))}")
            # 后端程序员开发接口并生成接口文档
            print("\n⚙️ 后端程序员正在开发 API 并生成接口文档...")
            be_agent.chat(json.dumps({
                "guide": backend_guide,
                "project_target": prd_content
            }, ensure_ascii=False))
            # 确保从后端代理获取API规范
            actual_api_spec = be_agent.api_spec
            # 如果后端代理没有正确设置api_spec，尝试从文件读取
            if not actual_api_spec:
                api_spec_path = os.path.join("output", "api_spec.json")
                if os.path.exists(api_spec_path):
                    try:
                        with open(api_spec_path, "r", encoding="utf-8") as f:
                            actual_api_spec = json.load(f)
                    except Exception as e:
                        print(f"❌ 读取API规范文件失败: {e}")
            print("✅ 后端开发完成")
            # 前端程序员基于实际接口文档开发页面
            print("\n🎨 前端程序员正在开发页面...")
            fe_agent.chat(json.dumps({
                "guide": frontend_guide,
                "project_target": prd_content,
                "api_spec": actual_api_spec
            }, ensure_ascii=False))
            print("✅ 前端开发完成")
            # 总结
            print("\n" + "=" * 50)
            print("🎉 项目开发完成！")
            print("📁 输出文件位置: output/")
            print("  - frontend/ 目录: 前端页面文件")
            print("  - backend/ 目录: 后端文件")
            print("  - api_spec.json: 接口文档")
            print("  - frontend_guide.md: 前端开发指导")
            print("  - backend_guide.md: 后端开发指导")
            print("=" * 50)
            # 询问是否继续
            continue_input = input("\n是否开始新项目？(y/n): ").strip().lower()
            if continue_input != 'y':
                print("👋 再见！")
                break
        except KeyboardInterrupt:
            print("\n\n👋 收到中断信号，再见！")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()
if __name__ == "__main__":
    main()