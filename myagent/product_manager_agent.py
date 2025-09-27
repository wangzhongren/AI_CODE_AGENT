from ai_agent_factory.agent.baseagent import BaseAgent
class ProductManagerAgent(BaseAgent):
    def __init__(self, basellm):
        system_prompt = (
            "你是一位资深的产品经理。你的任务是根据客户的描述，编写一份详细的产品需求文档（PRD）。"
            "PRD 应包括功能描述、用户流程、页面结构等内容。"
        )
        super().__init__(basellm, system_prompt, max_context=30)
    def todo(self, token: str):
        # 保存 PRD 内容到变量或文件中，供后续调用
        self.prd = token
        print("✅ 产品经理已完成 PRD 编写")
        print(self.prd)
    def token_deal(self, result: str):
        print(result, end='', flush=True)