# 智能项目开发系统

一个基于AI代理的自动化项目开发系统，通过多个专业角色的AI代理协作完成项目开发任务。

## 系统架构

- **Product Manager Agent**: 产品管理代理，负责制定产品需求文档(PRD)
- **Project Manager Agent**: 项目管理代理，负责制定开发指南和项目计划
- **Frontend Developer Agent**: 前端开发代理，负责前端应用的开发和实现
- **Backend Developer Agent**: 后端开发代理，负责后端服务的开发和实现
- **System Manager Agent**: 系统管理代理，负责协调各个代理和整体项目流程

## 技术栈

- Python 3.10+
- OpenAI LLM接口
- 自定义AI代理工厂框架
- Python-dotenv (环境变量管理)

## 环境配置

1. 复制 `.env.example` 文件并重命名为 `.env`
2. 在 `.env` 文件中配置以下环境变量：

```bash
api_key=your_openai_api_key
model_name=your_model_name
base_url=your_base_url
```

## 运行系统

```bash
python enhanced_main.py
```

## 使用说明

1. **初始阶段**：输入您的项目需求，系统将自动完成开发
2. **开发完成后**：可以输入修改需求以更新项目
3. **系统命令**：
   - `status` - 查看当前项目状态
   - `next` - 执行下一步开发
   - `quit` - 退出系统

## 功能特点

- 自动化项目开发流程
- 多代理协作模式
- 智能状态管理
- 支持需求变更和迭代开发
- 错误处理和异常恢复

## 项目状态跟踪

系统会自动跟踪以下开发阶段：
- PRD (产品需求文档) 完成状态
- 开发指南完成状态
- 后端开发完成状态
- 前端开发完成状态

## 开发流程

1. 用户提供需求
2. 产品经理代理生成PRD
3. 项目经理代理制定开发指南
4. 前后端开发代理并行开发
5. 系统协调并整合各部分工作

## 注意事项

- 需要有效的OpenAI API密钥
- 确保网络连接以调用LLM服务
- 系统会根据项目完成状态自动切换到修改模式
