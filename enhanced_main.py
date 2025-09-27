import json
import os
from ai_agent_factory.llms.base_llm_openai import OpenAILLM
from myagent.product_manager_agent import ProductManagerAgent
from myagent.frontend_developer_agent import FrontendDeveloperAgent
from myagent.backend_developer_agent import BackendDeveloperAgent
from myagent.project_manager_agent import ProjectManagerAgent
from myagent.system_manager_agent import SystemManagerAgent
from dotenv import load_dotenv

load_dotenv()

def main():
    # 初始化 LLM
    llm = OpenAILLM(
        api_key=os.getenv('api_key'),
        model_name=os.getenv('model_name'),
        base_url=os.getenv('base_url')
    )
    # 创建各个角色 Agents
    pm_agent = ProductManagerAgent(llm)
    pj_agent = ProjectManagerAgent(llm)
    fe_agent = FrontendDeveloperAgent(llm)
    be_agent = BackendDeveloperAgent(llm)
    # 组装 agents 字典
    agents = {
        'pm': pm_agent,
        'pj': pj_agent,
        'fe': fe_agent,
        'be': be_agent
    }
    # 创建全局管理者
    manager_agent = SystemManagerAgent(llm, agents)
    print("🚀 智能项目管理系统")
    print("=" * 50)
    print("使用说明：")
    print("1. 初始阶段：输入需求，系统自动完成开发")
    print("2. 开发完成后：可输入修改需求")
    print("3. 命令：'status'(状态) 'next'(下一步) 'quit'(退出)")
    print("=" * 50)
    # 标记项目是否已完成初始开发
    initial_development_done = False
    while True:
        try:
            user_input = input("\n🎯 您的指令: ").strip()
            if user_input.lower() == "quit":
                print("👋 再见！")
                break
            elif user_input.lower() == "status":
                manager_agent.report_status()
                continue
            elif user_input.lower() == "next":
                manager_agent.execute_next_step()
                # 检查是否初始开发已完成
                if (manager_agent.project_state['prd_completed'] and 
                    manager_agent.project_state['guides_completed'] and 
                    manager_agent.project_state['backend_completed'] and 
                    manager_agent.project_state['frontend_completed']):
                    initial_development_done = True
                    print("🎉 初始开发已完成！现在可以输入修改需求了。")
                continue
            elif not user_input:
                continue
            else:
                # 判断是初始需求还是修改需求
                if not initial_development_done:
                    # 初始开发阶段
                    if any(keyword in user_input for keyword in ['修改', '调整', '更新', '改']):
                        # 如果项目还没完成就提修改，先完成初始开发
                        print("📋 系统将先完成初始开发，然后处理您的修改需求...")
                        # 执行完整的开发流程
                        while not (manager_agent.project_state['prd_completed'] and 
                                  manager_agent.project_state['guides_completed'] and 
                                  manager_agent.project_state['backend_completed'] and 
                                  manager_agent.project_state['frontend_completed']):
                            manager_agent.execute_next_step()
                        initial_development_done = True
                        print("🎉 初始开发已完成！现在处理您的修改需求...")
                        # 继续处理修改需求
                        manager_agent.handle_change_request(user_input)
                    else:
                        # 正常需求输入
                        print("🤖 系统管理者正在处理您的需求...")
                        manager_agent.chat(user_input)
                    # 检查是否初始开发已完成
                    if (manager_agent.project_state['prd_completed'] and 
                        manager_agent.project_state['guides_completed'] and 
                        manager_agent.project_state['backend_completed'] and 
                        manager_agent.project_state['frontend_completed']):
                        initial_development_done = True
                        print("🎉 初始开发已完成！现在可以输入修改需求了。")
                else:
                    # 修改阶段
                    print("🔄 系统管理者正在分析您的修改需求...")
                    manager_agent.handle_change_request(user_input)
        except KeyboardInterrupt:
            print("\n\n👋 收到中断信号，再见！")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()
if __name__ == "__main__":
    main()