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
    print("1. 输入需求，系统自动完成开发")
    print("2. 开发完成后可输入修改需求")
    print("3. 命令：'status'(状态) 'next'(下一步) 'quit'(退出)")
    print("=" * 50)
    
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
                continue
            elif not user_input:
                continue
            else:
                # 所有用户输入都交给 SystemManagerAgent 处理
                # 它会自动判断是初始需求还是修改需求
                print("🤖 系统管理者正在处理您的需求...")
                
                # 检查项目状态来判断是初始需求还是修改需求
                if (manager_agent.project_state['prd_completed'] and 
                    manager_agent.project_state['guides_completed'] and 
                    manager_agent.project_state['backend_completed'] and 
                    manager_agent.project_state['frontend_completed']):
                    # 项目已完成，这是修改需求
                    print("🔄 识别为修改需求...")
                    manager_agent.handle_change_request(user_input)
                else:
                    # 项目未完成，这是初始需求
                    print("📝 识别为初始需求...")
                    manager_agent.chat(user_input)
                
        except KeyboardInterrupt:
            print("\n\n👋 收到中断信号，再见！")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()